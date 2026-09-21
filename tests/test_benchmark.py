import json
import subprocess
import sys
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import benchmark_outline as runner
from dataset import ROOT


@pytest.mark.parametrize("response", ["B", "b", " B. ", "**B**", "Answer: B", "B)"])
def test_explicit_mc_answer(bank, response):
    assert runner.grade(response, bank.items[0])["score"] == 1


def test_wrong_mc_answer(bank):
    result = runner.grade("A", bank.items[0])
    assert result["score"] == 0
    assert result["status"] == "incorrect"


@pytest.mark.parametrize(
    "response",
    [
        "",
        "A or B",
        "Not B",
        "B because I think so",
        "(B)",
        "The letter B appears in the question.",
        "B\nActually A",
        "B) +4",
        "Answer: B or C",
    ],
)
def test_no_guessing_or_substring_grading(bank, response):
    result = runner.grade(response, bank.items[0])
    assert result["score"] is None
    assert result["status"] == "needs_review"


@pytest.mark.parametrize(
    ("number", "response"),
    [
        (51, "**D8**"),
        (52, "Str 13 and Cha 13"),
        (55, "6,500 XP"),
        (61, "3 pounds"),
        (74, "1d10+10"),
    ],
)
def test_known_short_answers(bank, number, response):
    assert runner.grade(response, bank.items[number - 1])["score"] == 1


@pytest.mark.parametrize(
    "response", ["Strength 13 or Charisma 13", "Strength 13 and Charisma 13, or either one", "13"]
)
def test_incorrect_or_unrecognized_short_answers_require_review(bank, response):
    assert runner.grade(response, bank.items[51])["score"] is None


def test_scenarios_and_unverified_items_never_auto_score(bank):
    for item in bank.items:
        if item.metadata["type"] == "scenario" or item.metadata["review_status"] != "verified":
            assert runner.grade(item.answer, item)["score"] is None


def test_summary_does_not_count_pending_as_failures():
    results = [
        {"response": "B", "grade": {"status": "correct", "score": 1}},
        {"response": "A", "grade": {"status": "incorrect", "score": 0}},
        {"response": "explanation", "grade": {"status": "needs_review", "score": None}},
        {"response": None, "grade": {"status": "not_run", "score": None}},
    ]
    assert runner.summarize(results) == {
        "total_items": 4,
        "answered": 3,
        "automatically_scored": 2,
        "automatically_correct": 1,
        "needs_review": 1,
        "not_run": 1,
        "accuracy_on_automatically_scored": 0.5,
    }
    assert runner.summarize([])["accuracy_on_automatically_scored"] is None


def test_real_runner_pairs_ids_and_preserves_text(bank, tmp_path):
    # Nonconsecutive IDs must not be relabeled by list position.
    subset = replace(bank, items=(bank.items[6], bank.items[41]))
    client = Mock()
    client.generate.side_effect = ["B\n", "A"]
    output = tmp_path / "run"
    result = runner.run_benchmark(client, subset, output, model_name="test")
    assert [call.args[0] for call in client.generate.call_args_list] == [
        i.prompt for i in subset.items
    ]
    assert (output / "Q007.txt").read_text() == "B\n"
    assert (output / "Q042.txt").read_text() == "A"
    assert not (output / "Q001.txt").exists()
    assert result["status"] == "completed"
    assert result["summary"]["automatically_correct"] == 1
    assert json.loads((output / "results.json").read_text()) == result
    assert result["dataset_sha256"] == subset.fingerprint
    assert result["finished_at"] is not None


@pytest.mark.parametrize(
    "failure", [RuntimeError("model failed"), KeyboardInterrupt(), TypeError("bad")]
)
def test_partial_results_survive_failure(bank, tmp_path, failure):
    client = Mock()
    client.generate.side_effect = ["B", failure]
    output = tmp_path / "partial"
    with pytest.raises(type(failure)):
        runner.run_benchmark(client, bank, output, model_name="test")
    report = json.loads((output / "results.json").read_text())
    assert report["summary"]["answered"] == 1
    assert report["summary"]["not_run"] == 99
    assert report["status"] == (
        "interrupted" if isinstance(failure, KeyboardInterrupt) else "failed"
    )
    assert (output / "Q001.txt").read_text() == "B"
    assert not (output / "Q002.txt").exists()


def test_non_text_client_response(bank, tmp_path):
    with pytest.raises(TypeError, match="must be text"):
        runner.run_benchmark(
            Mock(generate=Mock(return_value=None)), bank, tmp_path / "run", model_name="bad"
        )


def test_never_overwrite_existing_output(bank, tmp_path):
    output = tmp_path / "old"
    output.mkdir()
    sentinel = output / "Q001.txt"
    sentinel.write_text("original")
    with pytest.raises(FileExistsError):
        runner.run_benchmark(runner.DryRunClient(), bank, output, model_name="test")
    assert sentinel.read_text() == "original"


def test_sdk_adapter_uses_config_and_documented_string(monkeypatch):
    result = Mock()
    result.__str__ = Mock(return_value="response content")
    model = Mock(respond=Mock(return_value=result))
    lms = SimpleNamespace(llm=Mock(return_value=model))
    monkeypatch.setattr(runner.importlib, "import_module", lambda name: lms)
    client = runner.LMStudioClient("test-model", 0.2, 500)
    assert client.generate("prompt") == "response content"
    lms.llm.assert_called_once_with("test-model")
    model.respond.assert_called_once_with("prompt", config={"temperature": 0.2, "maxTokens": 500})


def test_missing_sdk_error(monkeypatch):
    monkeypatch.setattr(runner.importlib, "import_module", Mock(side_effect=ImportError))
    with pytest.raises(RuntimeError, match="requirements.txt"):
        runner.LMStudioClient("test")


def test_validate_and_dry_run_never_contact_sdk(monkeypatch, tmp_path):
    sdk = Mock(side_effect=AssertionError("must stay offline"))
    monkeypatch.setattr(runner, "LMStudioClient", sdk)
    assert runner.main(["--validate-only"]) == 0
    output = tmp_path / "offline"
    assert runner.main(["--dry-run", "--output-dir", str(output)]) == 0
    report = json.loads((output / "results.json").read_text())
    assert len(list(output.glob("Q*.txt"))) == 100
    assert report["dry_run"] is True
    assert report["summary"]["automatically_scored"] == 0
    assert all(r["grade"]["status"] == "dry_run" for r in report["results"])
    sdk.assert_not_called()


def test_cli_live_path_with_fake_sdk(monkeypatch, tmp_path):
    monkeypatch.setattr(
        runner, "LMStudioClient", Mock(return_value=Mock(generate=Mock(return_value="B")))
    )
    monkeypatch.setattr(runner, "version", lambda name: "test-version")
    assert runner.main(["--model", "fake", "--output-dir", str(tmp_path / "run")]) == 0
    report = json.loads((tmp_path / "run/results.json").read_text())
    assert report["generation_config"]["lmstudio_sdk_version"] == "test-version"
    assert report["dry_run"] is False


def test_cli_missing_model(monkeypatch):
    monkeypatch.delenv("LM_STUDIO_MODEL", raising=False)
    with pytest.raises(SystemExit) as exc:
        runner.main([])
    assert exc.value.code == 2


@pytest.mark.parametrize(
    "args",
    [
        ["--temperature", "nan"],
        ["--temperature", "inf"],
        ["--temperature", "-1"],
        ["--max-tokens", "0"],
        ["--dry-run", "--validate-only"],
    ],
)
def test_cli_invalid_arguments(args):
    with pytest.raises(SystemExit) as exc:
        runner.main(args)
    assert exc.value.code == 2


def test_bad_dataset_fails_before_model(monkeypatch, tmp_path):
    model = Mock()
    monkeypatch.setattr(runner, "LMStudioClient", model)
    assert runner.main(["--model", "test", "--dataset-dir", str(tmp_path)]) == 1
    model.assert_not_called()


def test_cli_existing_output_fails_before_model(monkeypatch, tmp_path):
    model = Mock()
    monkeypatch.setattr(runner, "LMStudioClient", model)
    assert runner.main(["--model", "test", "--output-dir", str(tmp_path)]) == 1
    model.assert_not_called()


def test_cli_interrupt(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "run_benchmark", Mock(side_effect=KeyboardInterrupt))
    assert runner.main(["--dry-run", "--output-dir", str(tmp_path / "new")]) == 130


def test_cli_works_outside_repo_without_site_packages(tmp_path):
    result = subprocess.run(
        [sys.executable, "-S", str(ROOT / "benchmark_outline.py"), "--validate-only"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "Validated 100 items" in result.stdout


def test_manage_cli(monkeypatch, capsys):
    import manage_dataset

    monkeypatch.setattr(manage_dataset, "sync_documents", lambda **kwargs: ["stale.md"])
    assert manage_dataset.main(["--check"]) == 1
    assert "Stale" in capsys.readouterr().out
    assert manage_dataset.main([]) == 0
    monkeypatch.setattr(manage_dataset, "sync_documents", lambda **kwargs: [])
    assert manage_dataset.main(["--check"]) == 0
