"""Hosted adapters are tested without network, API keys, or billable inference."""

import io
import json
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.error import HTTPError, URLError

import pytest

import benchmark_outline as runner
import providers


def completion(text="B", stop="stop"):
    return {
        "choices": [{"message": {"content": text}, "finish_reason": stop}],
        "usage": {"prompt_tokens": 20, "completion_tokens": 1, "total_tokens": 21},
    }


def fake_http(client, data):
    response = io.BytesIO(json.dumps(data).encode())
    client._opener = Mock(open=Mock(return_value=response))
    return client._opener


def test_endpoint_request_is_fresh_and_auth_is_not_in_payload():
    client = providers.OpenAICompatibleClient(
        "served-model",
        "https://endpoint.example/v1/",
        api_key="test-secret",
        temperature=0.2,
        max_tokens=42,
        timeout=9,
    )
    opener = fake_http(client, completion())
    assert client.generate("Which rule?") == "B"
    request = opener.open.call_args.args[0]
    assert request.full_url == "https://endpoint.example/v1/chat/completions"
    assert request.method == "POST"
    assert request.get_header("Authorization") == "Bearer test-secret"
    assert json.loads(request.data) == {
        "model": "served-model",
        "messages": [{"role": "user", "content": "Which rule?"}],
        "max_tokens": 42,
        "temperature": 0.2,
        "stream": False,
    }
    assert opener.open.call_args.kwargs == {"timeout": 9}
    assert client.last_response_metadata == {
        "stop_reason": "stop",
        "requires_review": False,
        "usage": {"prompt_tokens": 20, "completion_tokens": 1, "total_tokens": 21},
    }
    opener = fake_http(client, completion("C"))
    client.generate("Second prompt")
    assert json.loads(opener.open.call_args.args[0].data)["messages"] == [
        {"role": "user", "content": "Second prompt"}
    ]


def test_unauthenticated_forwarding_and_default_temperature():
    client = providers.OpenAICompatibleClient(
        "model",
        "http://127.0.0.1:8000/v1",
        temperature=None,
        token_parameter="max_completion_tokens",
    )
    opener = fake_http(client, completion())
    client.generate("prompt")
    request = opener.open.call_args.args[0]
    assert request.get_header("Authorization") is None
    assert "temperature" not in json.loads(request.data)
    assert json.loads(request.data)["max_completion_tokens"] == 1024
    assert "max_tokens" not in json.loads(request.data)


@pytest.mark.parametrize(
    "url",
    [
        "https://host.example/v1",
        "http://localhost:8000/v1",
        "http://127.0.0.1:9000/api/v1",
        "http://[::1]:8000/v1",
    ],
)
def test_supported_endpoint_urls(url):
    assert providers.validate_base_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "",
        "host/v1",
        "ftp://host/v1",
        "http://remote.example/v1",
        "https://user:secret@host/v1",
        "https://host/v1?key=secret",
        "https://host/v1#secret",
        "https://host:bad/v1",
        "https://[invalid/v1",
        "https://host:0/v1",
        "https://host/a b/v1",
        "https://host/v1/chat/completions",
    ],
)
def test_bad_urls_fail_without_echoing_credentials(url):
    with pytest.raises(ValueError) as exc:
        providers.validate_base_url(url)
    assert "secret" not in str(exc.value)


@pytest.mark.parametrize("key", ["a\nb", "secret with spaces", "secret\t", "秘密", "\x7f"])
def test_bad_header_tokens(key):
    with pytest.raises(ValueError, match="API key"):
        providers.OpenAICompatibleClient("m", "https://host/v1", api_key=key)


def test_invalid_token_parameter():
    with pytest.raises(ValueError, match="token parameter"):
        providers.OpenAICompatibleClient("m", "https://host/v1", token_parameter="bad")


@pytest.mark.parametrize(
    "data",
    [
        None,
        [],
        {},
        {"choices": []},
        {"choices": [None]},
        {"choices": [{"message": None}]},
        completion(None),
        completion(""),
        completion("   "),
        completion([{"text": "B"}]),
        {"choices": [{"message": {"content": "B", "tool_calls": [{}]}}]},
        {"choices": [{}, {}]},
    ],
)
def test_malformed_completion_is_not_scored(data):
    client = providers.OpenAICompatibleClient("m", "https://host/v1")
    fake_http(client, data)
    with pytest.raises(providers.ProviderError, match="no single usable"):
        client.generate("p")


@pytest.mark.parametrize("status", [301, 302, 307, 400, 401, 429, 503])
def test_http_errors_do_not_leak_remote_details_or_retry(status):
    client = providers.OpenAICompatibleClient("m", "https://host/v1", api_key="SECRET")
    error = HTTPError("https://secret-url", status, "SECRET", {}, io.BytesIO(b"SECRET body"))
    client._opener = Mock(open=Mock(side_effect=error))
    with pytest.raises(providers.ProviderError) as exc:
        client.generate("p")
    assert str(status) in str(exc.value)
    assert "SECRET" not in str(exc.value)
    assert "secret-url" not in str(exc.value)
    client._opener.open.assert_called_once()
    assert error.fp.closed


@pytest.mark.parametrize(
    "error", [URLError("SECRET"), TimeoutError("SECRET"), OSError("SECRET"), ValueError("SECRET")]
)
def test_transport_errors_are_safe(error):
    client = providers.OpenAICompatibleClient("m", "https://host/v1")
    client._opener = Mock(open=Mock(side_effect=error))
    with pytest.raises(providers.ProviderError) as exc:
        client.generate("p")
    assert "SECRET" not in str(exc.value)


def test_invalid_json_is_safe():
    client = providers.OpenAICompatibleClient("m", "https://host/v1")
    client._opener = Mock(open=Mock(return_value=io.BytesIO(b"<html>SECRET login</html>")))
    with pytest.raises(providers.ProviderError, match="invalid JSON"):
        client.generate("p")


def test_redirect_handler_never_forwards_authorization():
    assert (
        providers._NoRedirects().redirect_request(
            None, None, 302, "redirect", {}, "https://other.example"
        )
        is None
    )


@pytest.mark.parametrize(
    "stop",
    [
        "length",
        "content_filter",
        "tool_calls",
        "function_call",
        None,
        [],
        "secret-unrecognized-value",
    ],
)
def test_endpoint_stop_reasons_and_usage_are_filtered(stop):
    client = providers.OpenAICompatibleClient("m", "https://host/v1")
    data = completion(stop=stop)
    data["usage"] = {
        "prompt_tokens": True,
        "completion_tokens": -1,
        "total_tokens": "SECRET",
        "api_key": "SECRET",
    }
    fake_http(client, data)
    client.generate("p")
    assert client.last_response_metadata["requires_review"] is True
    assert client.last_response_metadata["usage"] == {}
    assert "secret" not in json.dumps(client.last_response_metadata).lower()


def test_non_dict_usage():
    assert providers._usage(None, ("total_tokens",)) == {}


def mock_bedrock(monkeypatch, **kwargs):
    runtime = Mock()
    runtime.meta.region_name = "us-east-1"
    session = Mock(client=Mock(return_value=runtime))
    sdk = SimpleNamespace(Session=Mock(return_value=session), __version__="test-sdk")
    config = Mock(return_value="config")
    modules = {"boto3": sdk, "botocore.config": SimpleNamespace(Config=config)}
    monkeypatch.setattr(providers.importlib, "import_module", modules.__getitem__)
    client = providers.BedrockClient("profile-or-model-id", **kwargs)
    return client, runtime, sdk, config


def bedrock_response(stop="end_turn", content=None):
    return {
        "output": {
            "message": {
                "role": "assistant",
                "content": content if content is not None else [{"text": "B"}],
            }
        },
        "stopReason": stop,
        "usage": {"inputTokens": 20, "outputTokens": 1, "totalTokens": 21},
    }


def test_bedrock_credentials_config_and_messages(monkeypatch):
    client, runtime, sdk, config = mock_bedrock(
        monkeypatch,
        region="us-east-1",
        profile="research",
        temperature=0.3,
        max_tokens=50,
        timeout=10,
    )
    runtime.converse.return_value = bedrock_response(
        content=[
            {"reasoningContent": {"reasoningText": {"text": "private reasoning"}}},
            {"text": "B"},
            {"text": "Details"},
        ]
    )
    assert client.generate("prompt") == "B\nDetails"
    sdk.Session.assert_called_once_with(profile_name="research", region_name="us-east-1")
    config.assert_called_once_with(
        connect_timeout=10, read_timeout=10, retries={"mode": "standard", "total_max_attempts": 1}
    )
    runtime.converse.assert_called_once_with(
        modelId="profile-or-model-id",
        messages=[{"role": "user", "content": [{"text": "prompt"}]}],
        inferenceConfig={"maxTokens": 50, "temperature": 0.3},
    )
    assert client.region == "us-east-1"
    assert client.last_response_metadata["usage"]["totalTokens"] == 21
    assert client.last_response_metadata["requires_review"] is False


def test_bedrock_default_temperature(monkeypatch):
    client, runtime, _, _ = mock_bedrock(monkeypatch, temperature=None)
    runtime.converse.return_value = bedrock_response("stop_sequence")
    client.generate("p")
    assert "temperature" not in runtime.converse.call_args.kwargs["inferenceConfig"]
    assert client.last_response_metadata["requires_review"] is False


def test_missing_boto3(monkeypatch):
    monkeypatch.setattr(
        providers.importlib, "import_module", Mock(side_effect=ImportError("SECRET"))
    )
    with pytest.raises(providers.ProviderError, match="requirements-bedrock.txt"):
        providers.BedrockClient("m")


def test_bedrock_init_error(monkeypatch):
    module = SimpleNamespace(Session=Mock(side_effect=RuntimeError("SECRET")), Config=Mock())
    monkeypatch.setattr(providers.importlib, "import_module", lambda name: module)
    with pytest.raises(providers.ProviderError) as exc:
        providers.BedrockClient("m")
    assert "SECRET" not in str(exc.value)


@pytest.mark.parametrize(
    "code",
    ["AccessDeniedException", "ThrottlingException", "ValidationException", "SECRET", [], None],
)
def test_bedrock_service_error_is_safe(monkeypatch, code):
    client, runtime, _, _ = mock_bedrock(monkeypatch)
    error = RuntimeError("SECRET")
    error.response = {"Error": {"Code": code, "Message": "SECRET"}}
    runtime.converse.side_effect = error
    with pytest.raises(providers.ProviderError) as exc:
        client.generate("p")
    assert "SECRET" not in str(exc.value)
    runtime.converse.assert_called_once()


@pytest.mark.parametrize(
    "data",
    [
        None,
        {},
        {"output": None},
        bedrock_response(content=[]),
        bedrock_response(content="bad"),
        bedrock_response(content=[None]),
        bedrock_response(content=[{"text": 2}]),
        bedrock_response(content=[{"text": ""}]),
        bedrock_response(content=[{"toolUse": {}}]),
        bedrock_response(content=[{"reasoningContent": {}}]),
    ],
)
def test_bedrock_malformed_output(monkeypatch, data):
    client, runtime, _, _ = mock_bedrock(monkeypatch)
    runtime.converse.return_value = data
    with pytest.raises(providers.ProviderError, match="no usable text"):
        client.generate("p")


@pytest.mark.parametrize(
    "stop", ["max_tokens", "guardrail_intervened", "content_filtered", "tool_use", "unknown"]
)
def test_bedrock_incomplete_replies_need_review(monkeypatch, stop):
    client, runtime, _, _ = mock_bedrock(monkeypatch)
    runtime.converse.return_value = bedrock_response(stop)
    client.generate("p")
    assert client.last_response_metadata["requires_review"]


def test_limit_and_truncation_preserve_full_dataset_identity(bank, tmp_path):
    client = providers.OpenAICompatibleClient("m", "https://host/v1")
    fake_http(client, completion("B", "length"))
    report = runner.run_benchmark(
        client, bank, tmp_path / "run", model_name="m", provider="brev", limit=1
    )
    assert report["dataset_sha256"] == bank.fingerprint
    assert report["selected_ids"] == ["Q001"]
    assert report["summary"]["total_items"] == 1
    assert report["summary"]["automatically_scored"] == 0
    assert report["results"][0]["response"] == "B"
    assert report["results"][0]["grade"]["reason"] == "provider_completion_incomplete"


@pytest.mark.parametrize("limit", [0, 101])
def test_bad_limit_before_output(bank, tmp_path, limit):
    with pytest.raises(ValueError, match="limit"):
        runner.run_benchmark(
            runner.DryRunClient(), bank, tmp_path / "no-run", model_name="m", limit=limit
        )
    assert not (tmp_path / "no-run").exists()


@pytest.mark.parametrize("provider", ["brev", "openai-compatible", "bedrock"])
def test_hosted_offline_modes_need_no_credentials(monkeypatch, tmp_path, provider):
    unavailable = Mock(side_effect=AssertionError("must stay offline"))
    monkeypatch.setattr(runner, "OpenAICompatibleClient", unavailable)
    monkeypatch.setattr(runner, "BedrockClient", unavailable)
    assert runner.main(["--provider", provider, "--validate-only"]) == 0
    assert (
        runner.main(
            [
                "--provider",
                provider,
                "--dry-run",
                "--limit",
                "1",
                "--output-dir",
                str(tmp_path / "run"),
            ]
        )
        == 0
    )
    report = json.loads((tmp_path / "run/results.json").read_text())
    assert report["provider"] == provider
    assert report["summary"]["answered"] == 1
    assert report["provider_config"] is None
    unavailable.assert_not_called()


@pytest.mark.parametrize(
    "args",
    [
        ["--limit", "0"],
        ["--limit", "101"],
        ["--request-timeout", "nan"],
        ["--request-timeout", "0"],
        ["--temperature", "unknown"],
        ["--base-url", "https://host/v1"],
        ["--aws-profile", "demo"],
        ["--provider", "brev", "--model", "m"],
        ["--provider", "bedrock", "--token-parameter", "max_completion_tokens"],
    ],
)
def test_cli_rejects_bad_hosted_configuration(args):
    with pytest.raises(SystemExit) as exc:
        runner.main(args)
    assert exc.value.code == 2


def test_hosted_model_does_not_fall_back_to_lmstudio_env(monkeypatch):
    monkeypatch.setenv("LM_STUDIO_MODEL", "local-only")
    with pytest.raises(SystemExit) as exc:
        runner.main(["--provider", "bedrock"])
    assert exc.value.code == 2


def test_cli_missing_explicit_key_env(monkeypatch):
    monkeypatch.delenv("TEST_MISSING_KEY", raising=False)
    with pytest.raises(SystemExit) as exc:
        runner.main(
            [
                "--provider",
                "brev",
                "--model",
                "m",
                "--base-url",
                "https://host/v1",
                "--api-key-env",
                "TEST_MISSING_KEY",
            ]
        )
    assert exc.value.code == 2


def test_cli_brev_report_excludes_bearer_key(monkeypatch, tmp_path):
    monkeypatch.setenv("TEST_BEARER", "TOPSECRET")
    client = providers.OpenAICompatibleClient("m", "https://host/v1", api_key="TOPSECRET")
    fake_http(client, completion())
    factory = Mock(return_value=client)
    monkeypatch.setattr(runner, "OpenAICompatibleClient", factory)
    assert (
        runner.main(
            [
                "--provider",
                "brev",
                "--model",
                "m",
                "--base-url",
                "https://host/v1",
                "--api-key-env",
                "TEST_BEARER",
                "--temperature",
                "default",
                "--limit",
                "1",
                "--output-dir",
                str(tmp_path / "run"),
            ]
        )
        == 0
    )
    assert factory.call_args.kwargs["api_key"] == "TOPSECRET"
    assert factory.call_args.kwargs["temperature"] is None
    raw = (tmp_path / "run/results.json").read_text()
    assert "TOPSECRET" not in raw
    report = json.loads(raw)
    assert report["provider_config"]["base_url"] == "https://host/v1"
    assert "temperature" not in report["generation_config"]


def test_cli_bedrock_report_and_region(monkeypatch, tmp_path):
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    client = SimpleNamespace(generate=lambda prompt: "B", region="us-west-2", sdk_version="test")
    factory = Mock(return_value=client)
    monkeypatch.setattr(runner, "BedrockClient", factory)
    assert (
        runner.main(
            [
                "--provider",
                "bedrock",
                "--model",
                "inference-profile",
                "--aws-profile",
                "research",
                "--limit",
                "1",
                "--output-dir",
                str(tmp_path / "run"),
            ]
        )
        == 0
    )
    assert factory.call_args.kwargs["region"] == "us-west-2"
    assert factory.call_args.kwargs["profile"] == "research"
    report = json.loads((tmp_path / "run/results.json").read_text())
    assert report["provider_config"]["aws_region"] == "us-west-2"
    assert "research" not in json.dumps(report)


def test_failure_report_excludes_remote_secrets(bank, tmp_path):
    client = providers.OpenAICompatibleClient("m", "https://host/v1", api_key="TOPSECRET")
    response = io.BytesIO(json.dumps(completion()).encode())
    error = HTTPError("https://host/v1", 401, "TOPSECRET", {}, io.BytesIO(b"TOPSECRET"))
    client._opener = Mock(open=Mock(side_effect=[response, error]))
    with pytest.raises(providers.ProviderError):
        runner.run_benchmark(
            client,
            replace(bank, items=bank.items[:2]),
            tmp_path / "failed",
            model_name="m",
            provider="brev",
        )
    raw = (tmp_path / "failed/results.json").read_text()
    assert "TOPSECRET" not in raw
    report = json.loads(raw)
    assert report["status"] == "failed" and report["summary"]["answered"] == 1


def test_lmstudio_can_omit_temperature(monkeypatch):
    monkeypatch.setattr(
        runner.importlib, "import_module", lambda name: SimpleNamespace(llm=lambda model: Mock())
    )
    client = runner.LMStudioClient("m", temperature=None)
    assert client.config == {"maxTokens": 1024}
