"""Load the reviewed question bank and enforce its offline data contract."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
IDS = tuple(f"Q{n:03}" for n in range(1, 101))
RULES_INSTRUCTION = (
    "Use D&D fifth edition's 2014 rules with official errata, not the 2024 revision. "
    "Use a later revision of a feature only when the question explicitly requests it."
)
INSTRUCTIONS = {
    "multiple_choice": "Return exactly one answer letter: A, B, C, or D.",
    "short_answer": "Give a single word, number, or brief phrase.",
    "scenario": "Explain the rules and material conditions. Distinguish DM rulings from explicit rules.",
}


class DatasetError(ValueError):
    """The question bank is incomplete, inconsistent, or malformed."""


def normalize_answer(text: str) -> str:
    """Normalize presentation only; never remove negations, units, or extra claims."""
    text = unicodedata.normalize("NFKC", text).casefold().strip()
    text = text.replace("*", "").replace("`", "")
    return " ".join(text.split()).rstrip(".")


def read_entries(directory: Path) -> dict[str, str]:
    entries = {}
    for path in sorted(directory.iterdir()):
        if path.suffix.lower() != ".md":
            continue
        if path.name != f"{path.stem}.md" or path.stem not in IDS or not path.is_file():
            raise DatasetError(f"Invalid item filename: {path.name}; expected Q001.md–Q100.md")
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            raise DatasetError(f"Empty item: {path}")
        entries[path.stem] = text
    if not entries:
        raise DatasetError(f"No question-bank Markdown files in {directory}")
    return entries


@dataclass(frozen=True)
class Item:
    id: str
    question: str
    answer: str
    metadata: dict[str, Any]

    @property
    def prompt(self) -> str:
        return f"{RULES_INSTRUCTION}\n\n{self.question}\n\n{INSTRUCTIONS[self.metadata['type']]}"


@dataclass(frozen=True)
class Dataset:
    metadata: dict[str, Any]
    items: tuple[Item, ...]

    @property
    def fingerprint(self) -> str:
        payload = {
            "metadata": self.metadata,
            "items": [(i.id, i.question, i.answer, i.prompt) for i in self.items],
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def load_dataset(root: Path = ROOT) -> Dataset:
    """Validate all 100 pairs and audit metadata before any model is contacted."""
    questions = read_entries(root / "questions")
    answers = read_entries(root / "answers")
    try:
        metadata = json.loads((root / "dataset.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DatasetError(f"Invalid dataset.json: {exc}") from exc
    if not isinstance(metadata, dict) or metadata.get("schema_version") != 1:
        raise DatasetError("dataset.json must have schema_version 1")
    for key in ("dataset_version", "ruleset", "audited_on", "baseline_commit"):
        if not _nonempty_string(metadata.get(key)):
            raise DatasetError(f"Missing dataset field: {key}")
    records = metadata.get("items")
    if not isinstance(records, dict):
        raise DatasetError("Metadata items must be an object")
    for label, entries in (("questions", questions), ("answers", answers), ("metadata", records)):
        if set(entries) != set(IDS):
            missing = sorted(set(IDS) - set(entries))
            extra = sorted(set(entries) - set(IDS))
            raise DatasetError(f"{label}: missing IDs {missing}; unexpected IDs {extra}")
    sources = metadata.get("sources")
    if not isinstance(sources, dict) or not sources:
        raise DatasetError("Missing source registry")
    for name, source in sources.items():
        if (
            not isinstance(source, dict)
            or not all(_nonempty_string(source.get(k)) for k in ("title", "url", "access"))
            or not source["url"].startswith("https://")
        ):
            raise DatasetError(f"Invalid source: {name}")
    items = []
    for n, id in enumerate(IDS, 1):
        record = records[id]
        kind = "multiple_choice" if n <= 50 else "short_answer" if n <= 75 else "scenario"
        if not isinstance(record, dict) or record.get("type") != kind:
            raise DatasetError(f"{id}: wrong item type")
        if record.get("review_status") not in {"verified", "provisional", "interpretation"}:
            raise DatasetError(f"{id}: invalid review status")
        if record.get("change") not in {"retained", "question", "answer", "question_and_answer"}:
            raise DatasetError(f"{id}: invalid change status")
        for field in ("locator", "audit_note"):
            if not _nonempty_string(record.get(field)):
                raise DatasetError(f"{id}: missing {field}")
        refs = record.get("sources")
        if (
            not isinstance(refs, list)
            or not refs
            or any(not isinstance(ref, str) or ref not in sources for ref in refs)
        ):
            raise DatasetError(f"{id}: invalid source references")
        if not re.match(rf"^{n}\.\s", questions[id]):
            raise DatasetError(f"{id}: question number does not match its filename")
        if kind == "multiple_choice":
            if re.findall(r"(?<!\w)([A-D])\)", questions[id]) != list("ABCD"):
                raise DatasetError(f"{id}: expected exactly four options A–D")
            if answers[id] not in {"A", "B", "C", "D"}:
                raise DatasetError(f"{id}: answer must be one letter A–D")
        if kind != "scenario":
            aliases = record.get("accepted_answers")
            if (
                not isinstance(aliases, list)
                or not aliases
                or not all(_nonempty_string(a) for a in aliases)
                or normalize_answer(answers[id]) not in {normalize_answer(a) for a in aliases}
            ):
                raise DatasetError(f"{id}: answer missing from valid accepted_answers")
            if kind == "multiple_choice" and aliases != [answers[id]]:
                raise DatasetError(f"{id}: multiple-choice aliases must match the single key")
        else:
            rubric = record.get("rubric")
            if (
                not isinstance(rubric, list)
                or len(rubric) != 3
                or any(
                    not _nonempty_string(r) or not r.startswith(f"{i}:")
                    for i, r in enumerate(rubric)
                )
            ):
                raise DatasetError(f"{id}: expected rubric levels 0, 1, 2")
        items.append(Item(id, questions[id], answers[id], record))
    return Dataset(metadata, tuple(items))
