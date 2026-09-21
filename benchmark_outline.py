"""Run the 2014 D&D question bank against LM Studio, with conservative grading."""

from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import re
import sys
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Protocol

from dataset import ROOT, Dataset, Item, load_dataset, normalize_answer


class Client(Protocol):
    def generate(self, prompt: str) -> str: ...


class LMStudioClient:
    """Use the SDK's default local connection and a fresh prompt for each item."""

    def __init__(self, model_name: str, temperature: float = 0.0, max_tokens: int = 1024):
        try:
            lms = importlib.import_module("lmstudio")
        except ImportError as exc:
            raise RuntimeError(
                "Install LM Studio support: python -m pip install -r requirements.txt"
            ) from exc
        self.model = lms.llm(model_name)
        self.config = {"temperature": temperature, "maxTokens": max_tokens}

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
) -> dict:
    """Preserve each raw response and mark incomplete runs without overwriting runs."""
    output_dir.mkdir(parents=True, exist_ok=False)
    report = {
        "report_schema_version": 1,
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
            for i in dataset.items
        ],
    }
    _save_report(output_dir, report)
    try:
        for index, (item, result) in enumerate(
            zip(dataset.items, report["results"], strict=True), 1
        ):
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
            _save_report(output_dir, report)
            print(
                f"[{index}/{len(dataset.items)}] {item.id}: {result['grade']['status']}", flush=True
            )
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model", default=os.environ.get("LM_STUDIO_MODEL"), help="LM Studio model identifier"
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
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=1024)
    args = parser.parse_args(argv)
    if not math.isfinite(args.temperature) or args.temperature < 0 or args.max_tokens < 1:
        parser.error("temperature must be finite and nonnegative; max-tokens must be positive")
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
            parser.error("--model (or LM_STUDIO_MODEL) is required unless running offline")
        client = (
            DryRunClient()
            if args.dry_run
            else LMStudioClient(args.model, args.temperature, args.max_tokens)
        )
        config = (
            None
            if args.dry_run
            else {
                "temperature": args.temperature,
                "maxTokens": args.max_tokens,
                "lmstudio_sdk_version": version("lmstudio"),
                "other_settings": "LM Studio defaults; record model quantization and server settings separately",
            }
        )
        report = run_benchmark(
            client,
            dataset,
            args.output_dir,
            model_name=args.model or "dry-run",
            dry_run=args.dry_run,
            generation_config=config,
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
