"""Generate the booklets and audit ledger from the canonical files."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from dataset import ROOT, Dataset, load_dataset


def render_documents(dataset: Dataset) -> dict[str, str]:
    header = (
        f"Dataset **{dataset.metadata['dataset_version']}** · "
        f"{dataset.metadata['ruleset']}\n\n"
        "Generated from `questions/`, `answers/`, and `dataset.json`; "
        "edit those files, then run `python manage_dataset.py`.\n\n"
    )
    questions = ["# DMBench question booklet\n\n", header]
    answers = [
        "# DMBench answer key and scenario rubrics\n\n",
        header,
        "Provisional items require source verification before scoring. "
        "Scenarios always require review; see [the audit](docs/CONTENT_AUDIT.md).\n\n",
    ]
    sections = {
        1: "Multiple choice (Q001–Q050)",
        51: "Short answers (Q051–Q075)",
        76: "Scenarios (Q076–Q100)",
    }
    for n, item in enumerate(dataset.items, 1):
        if n in sections:
            for document in (questions, answers):
                document.append(f"## {sections[n]}\n\n")
        questions.append(item.question + "\n\n")
        answers.append(f"### {item.id}\n\n{item.answer}\n\n")
        meta = item.metadata
        citations = "; ".join(
            f"[{dataset.metadata['sources'][ref]['title']}]({dataset.metadata['sources'][ref]['url']})"
            for ref in meta["sources"]
        )
        answers.append(
            f"**Review:** {meta['review_status']}. **Rule locator:** {meta['locator']}.\n\nSources: {citations}\n\n"
        )
        if meta["type"] == "scenario":
            answers.append("\n".join(f"- {r}" for r in meta["rubric"]) + "\n\n")
    counts = Counter(i.metadata["review_status"] for i in dataset.items)
    changes = Counter(i.metadata["change"] for i in dataset.items)
    audit = [
        "# Content audit\n\n",
        header,
        f"Reviewed on **{dataset.metadata['audited_on']}** against baseline commit "
        f"`{dataset.metadata['baseline_commit']}`. All 100 items were inspected.\n\n",
        f"- Source-verified: **{counts['verified']}**\n",
        f"- Explicitly interpretive: **{counts['interpretation']}**\n",
        f"- Provisional, pending primary-source access: **{counts['provisional']}**\n\n",
        "These statuses describe the content audit, not model performance. "
        "Automated tests check data consistency and known regressions; they cannot prove a D&D ruling true. "
        "The audit is a source-backed editorial review, not an independent expert certification.\n\n",
        "## Changes and remaining work\n\n",
        f"{100 - changes['retained']} items have a changed question and/or answer; "
        f"{changes['retained']} retain both original texts. "
        "Reworded or replaced questions make version 2 scores incomparable with the old dataset. "
        "Originals remain available in Git at the baseline commit.\n\n",
        "The original multiple-choice bank contained wrong keys, a numeric key instead of a letter, "
        "questions with multiple correct choices, and stems with no correct choice. "
        "Scenario answers invented rules for feats, spell components, control limits, and armor. "
        "Ambiguous premises were narrowed; Q010, Q034, and Q073 were substantially reframed.\n\n",
        "The following full-text sources could not be accessed in this audit. "
        "Provisional corrections are recorded but excluded from automatic scoring. "
        "A reviewer with the listed 2014 books must check the question, answer, and conditions "
        "before changing its status to verified:\n\n",
    ]
    for item in dataset.items:
        if item.metadata["review_status"] == "provisional":
            audit.append(
                f"- **{item.id}** — {item.metadata['locator']}. {item.metadata['audit_note']}\n"
            )
    audit.extend(
        [
            "\nQ088 is intentionally an interpretation question: reward the explicit restrictions and "
            "recognition of the portal issue, not one forced teleportation ruling. "
            "Q079 excludes the disputed damage-modifier question from its rubric.\n\n",
            "## Method and sources\n\n",
            "Use the 2014 rules, applying official errata where they update the older SRD text. "
            "In particular, the Player's Handbook errata makes a simulacrum a construct; "
            "the SCAG errata supplies Q094's revised cantrip substitution. "
            "Book/page locators for inaccessible material are follow-up references, not proof it was read. "
            "Forum posts and current-edition replacements are not primary-source verification.\n\n",
        ]
    )
    for source in dataset.metadata["sources"].values():
        audit.append(f"- [{source['title']}]({source['url']}) — {source['access']}.\n")
    audit.append(
        "\n## Item-by-item ledger\n\n| Item | Status | Changed | Finding and rule locator |\n|---|---|---|---|\n"
    )
    for item in dataset.items:
        m = item.metadata
        audit.append(
            f"| [{item.id}](../questions/{item.id}.md) / [answer](../answers/{item.id}.md) | {m['review_status']} | {m['change']} | {m['audit_note']} **Source:** {', '.join(m['sources'])}; {m['locator']}. |\n"
        )
    return {
        "dnd_benchmark_questions.md": "".join(questions).rstrip() + "\n",
        "dnd_benchmark_answers.md": "".join(answers).rstrip() + "\n",
        "docs/CONTENT_AUDIT.md": "".join(audit).rstrip() + "\n",
    }


def sync_documents(root: Path = ROOT, *, check: bool = False) -> list[str]:
    stale = []
    for name, content in render_documents(load_dataset(root)).items():
        path = root / name
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            stale.append(name)
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
    return stale


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="Fail if generated documents are stale"
    )
    args = parser.parse_args(argv)
    stale = sync_documents(check=args.check)
    if stale:
        print(("Stale: " if args.check else "Updated: ") + ", ".join(stale))
    else:
        print("Generated documents are up to date.")
    return int(args.check and bool(stale))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
