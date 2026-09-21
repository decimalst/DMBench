import json
from dataclasses import replace

import pytest

from dataset import IDS, DatasetError, load_dataset, read_entries
from manage_dataset import render_documents, sync_documents


def test_complete_bank_and_review_counts(bank):
    assert tuple(i.id for i in bank.items) == IDS
    assert [
        sum(i.metadata["type"] == kind for i in bank.items)
        for kind in ("multiple_choice", "short_answer", "scenario")
    ] == [50, 25, 25]
    assert {i.id for i in bank.items if i.metadata["review_status"] == "provisional"} == {
        "Q058",
        "Q067",
        "Q068",
        "Q069",
        "Q081",
        "Q096",
    }
    assert [i.id for i in bank.items if i.metadata["review_status"] == "interpretation"] == ["Q088"]


@pytest.mark.parametrize("directory", ["questions", "answers"])
@pytest.mark.parametrize("name", ["Q000.md", "Q101.md", "q001.md", "notes.md", "Q001.MD"])
def test_invalid_filenames(copied_bank, directory, name):
    # Remove the canonical name first on case-insensitive macOS filesystems.
    if name.lower() == "q001.md":
        (copied_bank / directory / "Q001.md").unlink()
    (copied_bank / directory / name).write_text("bad", encoding="utf-8")
    with pytest.raises(DatasetError, match="filename"):
        load_dataset(copied_bank)


def test_markdown_named_directory(copied_bank):
    (copied_bank / "questions/Q001.md").unlink()
    (copied_bank / "questions/Q001.md").mkdir()
    with pytest.raises(DatasetError, match="filename"):
        load_dataset(copied_bank)


@pytest.mark.parametrize("directory", ["questions", "answers"])
def test_empty_item(copied_bank, directory):
    (copied_bank / directory / "Q003.md").write_text(" \n", encoding="utf-8")
    with pytest.raises(DatasetError, match="Empty item"):
        load_dataset(copied_bank)


def test_empty_directory(tmp_path):
    with pytest.raises(DatasetError, match="No question-bank"):
        read_entries(tmp_path)


def test_non_markdown_ignored(copied_bank):
    (copied_bank / "questions/.DS_Store").write_text("junk", encoding="utf-8")
    assert len(load_dataset(copied_bank).items) == 100


@pytest.mark.parametrize("directory", ["questions", "answers"])
def test_missing_pair_fails_even_if_counts_match(copied_bank, directory):
    # Equal counts in two directories do not guarantee matching identities.
    (copied_bank / directory / "Q003.md").unlink()
    other = "answers" if directory == "questions" else "questions"
    (copied_bank / other / "Q004.md").unlink()
    with pytest.raises(DatasetError, match="missing IDs"):
        load_dataset(copied_bank)


@pytest.mark.parametrize("text", ["[]", "{", '{"schema_version": 2}'])
def test_bad_metadata_document(copied_bank, text):
    (copied_bank / "dataset.json").write_text(text, encoding="utf-8")
    with pytest.raises(DatasetError):
        load_dataset(copied_bank)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("type", "scenario"),
        ("review_status", "made_up"),
        ("change", "unknown"),
        ("sources", []),
        ("sources", ["missing"]),
        ("sources", [{}]),
        ("locator", ""),
        ("audit_note", None),
        ("accepted_answers", ["A"]),
        ("accepted_answers", ["B", "C"]),
        ("accepted_answers", [""]),
        ("accepted_answers", [3]),
    ],
)
def test_invalid_item_metadata(copied_bank, field, value):
    path = copied_bank / "dataset.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["items"]["Q001"][field] = value
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(DatasetError, match="Q001"):
        load_dataset(copied_bank)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("dataset_version", ""),
        ("items", []),
        ("items", {}),
        ("sources", {}),
        ("sources", {"bad": {"url": "http://bad", "title": "Bad", "access": "public"}}),
        ("sources", {"bad": []}),
    ],
)
def test_invalid_top_level_metadata(copied_bank, field, value):
    path = copied_bank / "dataset.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data[field] = value
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(DatasetError):
        load_dataset(copied_bank)


@pytest.mark.parametrize("rubric", [None, [], ["0: x", "1: y", "3: z"], [0, 1, 2]])
def test_invalid_rubric(copied_bank, rubric):
    path = copied_bank / "dataset.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["items"]["Q076"]["rubric"] = rubric
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(DatasetError, match="rubric"):
        load_dataset(copied_bank)


@pytest.mark.parametrize(
    ("file", "text", "message"),
    [
        ("questions/Q001.md", "2. Wrong ID", "number"),
        ("questions/Q001.md", "1. Missing options", "four options"),
        ("questions/Q001.md", "1. A) a B) b C) c D) d A) extra", "four options"),
        ("answers/Q045.md", "8", "one letter"),
    ],
)
def test_question_and_key_contract(copied_bank, file, text, message):
    (copied_bank / file).write_text(text, encoding="utf-8")
    with pytest.raises(DatasetError, match=message):
        load_dataset(copied_bank)


def test_fingerprint_covers_questions_answers_and_metadata(bank, copied_bank):
    original = bank.fingerprint
    item = bank.items[0]
    changed = replace(bank, items=(replace(item, answer="C"), *bank.items[1:]))
    assert changed.fingerprint != original
    changed = replace(bank, items=(replace(item, question="different"), *bank.items[1:]))
    assert changed.fingerprint != original
    changed = replace(bank, metadata={**bank.metadata, "dataset_version": "next"})
    assert changed.fingerprint != original
    assert load_dataset(copied_bank).fingerprint == original


def test_prompts_are_rules_scoped_and_do_not_leak_answers(bank):
    for item in bank.items:
        assert "2014" in item.prompt
        assert item.question in item.prompt
        assert "audit_note" not in item.prompt
        if item.metadata["type"] == "scenario":
            assert item.answer not in item.prompt


def test_generated_documents_match_canonical_bank(bank):
    from dataset import ROOT

    for path, expected in render_documents(bank).items():
        assert (ROOT / path).read_text(encoding="utf-8") == expected


def test_sync_check_does_not_write_and_generation_is_idempotent(copied_bank):
    assert len(sync_documents(copied_bank, check=True)) == 3
    assert not (copied_bank / "dnd_benchmark_questions.md").exists()
    assert len(sync_documents(copied_bank)) == 3
    assert sync_documents(copied_bank, check=True) == []
    assert sync_documents(copied_bank) == []
    (copied_bank / "answers/Q001.md").write_text("C\n", encoding="utf-8")
    path = copied_bank / "dataset.json"
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta["items"]["Q001"]["accepted_answers"] = ["C"]
    path.write_text(json.dumps(meta), encoding="utf-8")
    assert "dnd_benchmark_answers.md" in sync_documents(copied_bank, check=True)
