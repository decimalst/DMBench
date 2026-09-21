"""Run the 2014 D&D question bank against local or hosted models."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import sys
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Protocol

from dataset import ROOT, Dataset, Item, load_dataset, normalize_answer
from providers import BedrockClient, OpenAICompatibleClient, validate_settings


class Client(Protocol):
    def generate(self, prompt: str) -> str: ...


class LMStudioClient:
    """Use the SDK's default local connection and a fresh prompt for each item."""

    def __init__(self, model_name: str, temperature: float | None = 0.0, max_tokens: int = 1024):
        try:
            lms = importlib.import_module("lmstudio")
        except ImportError as exc:
            raise RuntimeError(
                "Install LM Studio support: python -m pip install -r requirements.txt"
            ) from exc
        self.model = lms.llm(model_name)
        self.config = {"maxTokens": max_tokens}
        if temperature is not None:
            self.config["temperature"] = temperature

    def generate(self, prompt: str) -> str:
        # PredictionResult.__str__ is the SDK's documented text interface.
        return str(self.model.respond(prompt, config=self.config))


class DryRunClient:
    def generate(self, prompt: str) -> str:
        return "[DRY RUN: no model was queried]"


def grade(response: str, item: Item) -> dict:
    """Score a definite MC choice; accept known short answers; otherwise defer."""
    result = {"status": "needs_review", "score": None, "reason": "manual_scenario"}
    if item.metadata["review_status"] != "verified":
        result["reason"] = item.metadata["review_status"]
        return result
    if item.metadata["type"] == "multiple_choice":
        # Full match prevents guessing from reasoning, multiple options, or negations.
        text = normalize_answer(response)
        match = re.fullmatch(r"(?:answer:\s*)?([a-d])[.)]?", text)
        if not match:
            result["reason"] = "unrecognized_choice"
            return result
        correct = match[1].upper() == item.answer
        return {
            "status": "correct" if correct else "incorrect",
            "score": int(correct),
            "reason": "explicit_choice",
        }
    if item.metadata["type"] == "short_answer":
        if normalize_answer(response) in {
            normalize_answer(a) for a in item.metadata["accepted_answers"]
        }:
            return {"status": "correct", "score": 1, "reason": "accepted_short_answer"}
        result["reason"] = "unrecognized_short_answer"
    return result


def summarize(results: list[dict]) -> dict:
    """Keep pending/unreviewed items outside the automatically scored denominator."""
    scored = [r for r in results if r["grade"]["score"] is not None]
    correct = sum(r["grade"]["score"] for r in scored)
    return {
        "total_items": len(results),
        "answered": sum(r["response"] is not None for r in results),
        "automatically_scored": len(scored),
        "automatically_correct": correct,
        "needs_review": sum(r["grade"]["status"] == "needs_review" for r in results),
        "not_run": sum(r["grade"]["status"] == "not_run" for r in results),
        # This is explicitly not a whole-benchmark accuracy estimate.
        "accuracy_on_automatically_scored": correct / len(scored) if scored else None,
    }


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _save_report(output: Path, report: dict) -> None:
    report["summary"] = summarize(report["results"])
    temporary = output / "results.json.tmp"
    temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(output / "results.json")


def run_benchmark(
    client: Client,
    dataset: Dataset,
    output_dir: Path,
    *,
    model_name: str,
    dry_run: bool = False,
    generation_config: dict | None = None,
    provider: str = "lmstudio",
    provider_config: dict | None = None,
    limit: int | None = None,
) -> dict:
    """Preserve each raw response and mark incomplete runs without overwriting runs."""
    if limit is not None and not 1 <= limit <= len(dataset.items):
        raise ValueError("limit must be between 1 and the dataset item count")
    items = dataset.items[:limit]
    output_dir.mkdir(parents=True, exist_ok=False)
    report = {
        "report_schema_version": 2,
        "provider": provider,
        "provider_config": provider_config,
        "selected_ids": [item.id for item in items],
        "dataset_version": dataset.metadata["dataset_version"],
        "dataset_sha256": dataset.fingerprint,
        "ruleset": dataset.metadata["ruleset"],
        "model": model_name,
        "dry_run": dry_run,
        "generation_config": generation_config,
        "python_version": sys.version,
        "started_at": _now(),
        "finished_at": None,
        "status": "running",
        "sources": dataset.metadata["sources"],
        "results": [
            {
                "id": i.id,
                "prompt": i.prompt,
                "reference_answer": i.answer,
                "audit": i.metadata,
                "response": None,
                "grade": {"status": "not_run", "score": None, "reason": "not_run"},
            }
            for i in items
        ],
    }
    _save_report(output_dir, report)
    try:
        for index, (item, result) in enumerate(zip(items, report["results"], strict=True), 1):
            response = client.generate(item.prompt)
            if not isinstance(response, str):
                raise TypeError(f"{item.id}: model response must be text")
            (output_dir / f"{item.id}.txt").write_text(response, encoding="utf-8")
            result["response"] = response
            result["grade"] = (
                {"status": "dry_run", "score": None, "reason": "dry_run"}
                if dry_run
                else grade(response, item)
            )
            response_metadata = getattr(client, "last_response_metadata", None)
            if isinstance(response_metadata, dict) and not dry_run:
                result["provider_response"] = response_metadata.copy()
                if response_metadata.get("requires_review"):
                    result["grade"] = {
                        "status": "needs_review",
                        "score": None,
                        "reason": "provider_completion_incomplete",
                    }
            _save_report(output_dir, report)
            print(f"[{index}/{len(items)}] {item.id}: {result['grade']['status']}", flush=True)
    except (Exception, KeyboardInterrupt) as exc:
        report["status"] = "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"
        report["error"] = f"{type(exc).__name__}: {exc}"
        report["finished_at"] = _now()
        _save_report(output_dir, report)
        raise
    report["status"] = "completed"
    report["finished_at"] = _now()
    _save_report(output_dir, report)
    return report


def parse_temperature(value: str) -> float | None:
    if value == "default":
        return None
    try:
        return float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("temperature must be a number or 'default'") from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider",
        choices=["lmstudio", "openai-compatible", "brev", "bedrock"],
        default="lmstudio",
    )
    parser.add_argument("--model", help="Provider model ID or Bedrock inference profile ID/ARN")
    parser.add_argument(
        "--base-url", help="OpenAI-compatible API root, including /v1 where required"
    )
    parser.add_argument(
        "--api-key-env",
        default="DMBENCH_API_KEY",
        help="Environment variable holding the endpoint's bearer token (optional)",
    )
    parser.add_argument(
        "--token-parameter",
        choices=["max_tokens", "max_completion_tokens"],
        default="max_tokens",
        help="Token-limit field for OpenAI-compatible endpoints",
    )
    parser.add_argument("--aws-region", help="Bedrock region; defaults to AWS region configuration")
    parser.add_argument(
        "--aws-profile",
        help="Optional AWS named profile; otherwise use the standard credential chain",
    )
    parser.add_argument(
        "--request-timeout",
        type=float,
        default=120.0,
        help="Hosted request socket timeout in seconds; no automatic inference retries",
    )
    parser.add_argument(
        "--limit", type=int, help="Run only the first N questions (1–100), for a smoke test"
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=ROOT,
        help="Root containing questions, answers, and dataset.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("report"),
        help="New directory for this run (must not exist)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--validate-only", action="store_true", help="Validate data offline and exit")
    mode.add_argument(
        "--dry-run", action="store_true", help="Exercise reports offline; no scores or model calls"
    )
    parser.add_argument(
        "--temperature",
        type=parse_temperature,
        default=0.0,
        help="Sampling temperature, or default to omit the parameter",
    )
    parser.add_argument("--max-tokens", type=int, default=1024)
    args = parser.parse_args(argv)
    try:
        validate_settings(args.temperature, args.max_tokens, args.request_timeout)
    except ValueError as exc:
        parser.error(str(exc))
    if args.limit is not None and not 1 <= args.limit <= 100:
        parser.error("limit must be between 1 and 100")
    if args.provider == "lmstudio":
        args.model = args.model or os.environ.get("LM_STUDIO_MODEL")
    if args.provider not in {"brev", "openai-compatible"} and (
        args.base_url
        or args.api_key_env != "DMBENCH_API_KEY"
        or args.token_parameter != "max_tokens"
    ):
        parser.error(
            "base-url, api-key-env, and token-parameter apply only to OpenAI-compatible/Brev endpoints"
        )
    if args.provider != "bedrock" and (args.aws_region or args.aws_profile):
        parser.error("aws-region and aws-profile apply only to Bedrock")
    try:
        dataset = load_dataset(args.dataset_dir)
        provisional = [i.id for i in dataset.items if i.metadata["review_status"] == "provisional"]
        print(
            f"Validated {len(dataset.items)} items; dataset {dataset.metadata['dataset_version']}."
        )
        print(
            f"Source verification pending (excluded from automatic scoring): {', '.join(provisional) or 'none'}"
        )
        if args.validate_only:
            return 0
        if args.output_dir.exists():
            raise FileExistsError(
                f"Output directory already exists: {args.output_dir}. Choose a new run directory."
            )
        if not args.dry_run and not args.model:
            parser.error(
                "--model is required unless running offline (LM Studio also accepts LM_STUDIO_MODEL)"
            )
        provider_config = None
        config = None
        if args.dry_run:
            client = DryRunClient()
        else:
            config = {"maxTokens": args.max_tokens}
            if args.temperature is not None:
                config["temperature"] = args.temperature
            if args.provider == "lmstudio":
                client = LMStudioClient(args.model, args.temperature, args.max_tokens)
                config["lmstudio_sdk_version"] = version("lmstudio")
            elif args.provider in {"brev", "openai-compatible"}:
                if not args.base_url:
                    parser.error("--base-url is required for hosted OpenAI-compatible/Brev runs")
                key = os.environ.get(args.api_key_env)
                if args.api_key_env != "DMBENCH_API_KEY" and not key:
                    parser.error(
                        "The explicitly selected API key environment variable is unset or empty"
                    )
                client = OpenAICompatibleClient(
                    args.model,
                    args.base_url,
                    api_key=key,
                    temperature=args.temperature,
                    max_tokens=args.max_tokens,
                    timeout=args.request_timeout,
                    token_parameter=args.token_parameter,
                )
                provider_config = {
                    "base_url": client.base_url,
                    "request_timeout_seconds": args.request_timeout,
                    "token_parameter": args.token_parameter,
                    "inference_attempts": 1,
                }
            else:
                client = BedrockClient(
                    args.model,
                    region=args.aws_region or os.environ.get("AWS_REGION"),
                    profile=args.aws_profile,
                    temperature=args.temperature,
                    max_tokens=args.max_tokens,
                    timeout=args.request_timeout,
                )
                provider_config = {
                    "aws_region": client.region,
                    "boto3_version": client.sdk_version,
                    "request_timeout_seconds": args.request_timeout,
                    "inference_attempts": 1,
                }
        report = run_benchmark(
            client,
            dataset,
            args.output_dir,
            model_name=args.model or "dry-run",
            dry_run=args.dry_run,
            generation_config=config,
            provider=args.provider,
            provider_config=provider_config,
            limit=args.limit,
        )
        print(json.dumps(report["summary"], indent=2))
        print(f"Saved report: {args.output_dir / 'results.json'}")
        return 0
    except KeyboardInterrupt:
        print(
            "Interrupted; completed responses are preserved in the run directory.", file=sys.stderr
        )
        return 130
    except Exception as exc:
        print(f"Benchmark failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover - exercised by subprocess tests
    raise SystemExit(main())
