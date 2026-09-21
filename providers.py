"""Hosted text-generation adapters. Imports and credentials are resolved on demand."""

from __future__ import annotations

import importlib
import json
import math
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class ProviderError(RuntimeError):
    """A safe-to-report error that excludes credentials and remote error bodies."""


def validate_settings(temperature: float | None, max_tokens: int, timeout: float) -> None:
    if temperature is not None and (not math.isfinite(temperature) or temperature < 0):
        raise ValueError("temperature must be finite and nonnegative, or 'default'")
    if max_tokens < 1 or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("max-tokens and request-timeout must be positive and finite")


def validate_base_url(value: str) -> str:
    """Require an explicit API root; reject credential-bearing URL components."""
    try:
        url = urlsplit(value)
        valid = (
            url.scheme in {"https", "http"}
            and url.hostname
            and url.port != 0
            and url.username is None
            and url.password is None
            and not url.query
            and not url.fragment
            and not re.search(r"\s", value)
            and (url.scheme == "https" or url.hostname in {"localhost", "127.0.0.1", "::1"})
            and not url.path.rstrip("/").endswith("/chat/completions")
        )
    except ValueError:
        valid = False
    if not valid:
        raise ValueError(
            "base-url must be an HTTPS API root (usually ending /v1), without credentials, "
            "query, fragment, or /chat/completions; HTTP is allowed only on loopback hosts"
        )
    return url.geturl().rstrip("/")


class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # In particular, never forward a bearer token to a redirected login/other host.
        return None


def _usage(raw: object, keys: tuple[str, ...]) -> dict[str, int]:
    if not isinstance(raw, dict):
        return {}
    return {k: raw[k] for k in keys if type(raw.get(k)) is int and raw[k] >= 0}


def _stop_reason(value: object, allowed: set[str]) -> str:
    return value if isinstance(value, str) and value in allowed else "unknown"


class OpenAICompatibleClient:
    """Non-streaming /chat/completions, including Brev-hosted NIM/vLLM servers.

    No OpenAI account or SDK is needed. There is deliberately no default endpoint
    and no implicit retry or fallback to a different hosted service.
    """

    def __init__(
        self,
        model_name: str,
        base_url: str,
        *,
        api_key: str | None = None,
        temperature: float | None = 0.0,
        max_tokens: int = 1024,
        timeout: float = 120.0,
        token_parameter: str = "max_tokens",
    ):
        validate_settings(temperature, max_tokens, timeout)
        self.base_url = validate_base_url(base_url)
        if token_parameter not in {"max_tokens", "max_completion_tokens"}:
            raise ValueError("Unsupported token parameter")
        if api_key and (
            not api_key.isascii() or any(ord(c) < 33 or ord(c) == 127 for c in api_key)
        ):
            raise ValueError(
                "The API key must be an ASCII token without whitespace/control characters"
            )
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.token_parameter = token_parameter
        self._api_key = api_key
        self._opener = build_opener(_NoRedirects())
        self.last_response_metadata: dict = {}

    def generate(self, prompt: str) -> str:
        self.last_response_metadata = {}
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            self.token_parameter: self.max_tokens,
            "stream": False,
        }
        if self.temperature is not None:
            payload["temperature"] = self.temperature
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        request = Request(
            self.base_url + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                data = json.loads(response.read())
        except HTTPError as exc:
            status = exc.code
            exc.close()
            raise ProviderError(
                f"Endpoint returned HTTP {status}; check authentication, model, quota, and API URL. "
                "Redirects are not followed; browser-login tunnel URLs need an API route or port forwarding."
            ) from None
        except (URLError, OSError, ValueError):
            raise ProviderError(
                "Endpoint request failed or returned invalid JSON; check connectivity, timeout, and API URL."
            ) from None
        try:
            choices = data["choices"]
            if len(choices) != 1:
                raise ValueError
            choice = choices[0]
            message = choice["message"]
            text = message["content"]
            if not isinstance(text, str) or not text.strip() or message.get("tool_calls"):
                raise ValueError
            stop = _stop_reason(
                choice.get("finish_reason"),
                {"stop", "length", "content_filter", "tool_calls", "function_call"},
            )
            self.last_response_metadata = {
                "stop_reason": stop,
                "requires_review": stop != "stop",
                "usage": _usage(
                    data.get("usage"), ("prompt_tokens", "completion_tokens", "total_tokens")
                ),
            }
            return text
        except (KeyError, IndexError, TypeError, ValueError, AttributeError):
            raise ProviderError(
                "Endpoint returned no single usable text completion (or requested tool use)."
            ) from None


class BedrockClient:
    """AWS Bedrock Converse with Boto3's credential chain and no inference retries."""

    def __init__(
        self,
        model_name: str,
        *,
        region: str | None = None,
        profile: str | None = None,
        temperature: float | None = 0.0,
        max_tokens: int = 1024,
        timeout: float = 120.0,
    ):
        validate_settings(temperature, max_tokens, timeout)
        try:
            boto3 = importlib.import_module("boto3")
            config_type = importlib.import_module("botocore.config").Config
        except ImportError:
            raise ProviderError(
                "Install Bedrock support: python -m pip install -r requirements-bedrock.txt"
            ) from None
        self.model_name = model_name
        self.config = {"maxTokens": max_tokens}
        if temperature is not None:
            self.config["temperature"] = temperature
        self.last_response_metadata: dict = {}
        try:
            session = boto3.Session(profile_name=profile, region_name=region)
            self.client = session.client(
                "bedrock-runtime",
                config=config_type(
                    connect_timeout=timeout,
                    read_timeout=timeout,
                    retries={"mode": "standard", "total_max_attempts": 1},
                ),
            )
            self.region = self.client.meta.region_name
            self.sdk_version = boto3.__version__
        except Exception:
            raise ProviderError(
                "Bedrock initialization failed; check AWS profile, credentials, and region."
            ) from None

    def generate(self, prompt: str) -> str:
        self.last_response_metadata = {}
        try:
            data = self.client.converse(
                modelId=self.model_name,
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig=self.config,
            )
        except Exception as exc:
            # SDK error strings can embed remote payloads; only expose known service codes.
            error = getattr(exc, "response", {})
            code = error.get("Error", {}).get("Code") if isinstance(error, dict) else None
            known = {
                "AccessDeniedException",
                "ValidationException",
                "ThrottlingException",
                "ModelTimeoutException",
                "ResourceNotFoundException",
                "ServiceUnavailableException",
                "ModelNotReadyException",
                "ExpiredTokenException",
            }
            safe_code = code if isinstance(code, str) and code in known else "request_failed"
            raise ProviderError(
                f"Bedrock {safe_code}; check AWS credentials, region, model access, supported parameters, and quota."
            ) from None
        try:
            blocks = data["output"]["message"]["content"]
            if not isinstance(blocks, list) or any("toolUse" in block for block in blocks):
                raise ValueError
            texts = [block["text"] for block in blocks if "text" in block]
            if (
                not texts
                or not all(isinstance(t, str) for t in texts)
                or not "".join(texts).strip()
            ):
                raise ValueError
            stop = _stop_reason(
                data.get("stopReason"),
                {
                    "end_turn",
                    "stop_sequence",
                    "max_tokens",
                    "tool_use",
                    "guardrail_intervened",
                    "content_filtered",
                },
            )
            self.last_response_metadata = {
                "stop_reason": stop,
                "requires_review": stop not in {"end_turn", "stop_sequence"},
                "usage": _usage(data.get("usage"), ("inputTokens", "outputTokens", "totalTokens")),
            }
            return "\n".join(texts)
        except (KeyError, TypeError, ValueError, AttributeError):
            raise ProviderError(
                "Bedrock returned no usable text completion (or requested tool use)."
            ) from None
