import sys, pathlib; sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from benchmark_outline import load_questions, load_answers, run_benchmark, grade

class DummyClient:
    """Simple stand-in for LMStudioClient used in tests."""

    def __init__(self):
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return f"response {len(self.prompts)}"


def test_load_questions(tmp_path):
    (tmp_path / "Q001.md").write_text("First?")
    (tmp_path / "Q055.md").write_text("Second?")
    (tmp_path / "Q080.md").write_text("Third?")

    questions = load_questions(str(tmp_path))
    assert len(questions) == 3
    assert questions[0].endswith("Choose the one best answer (A–D).")
    assert questions[1].endswith("Give a single word, number, or brief phrase.")
    assert questions[2].endswith(
        "Explain what happens according to official rules. A thorough answer cites page numbers or core-rule sources where possible."
    )


def test_load_answers(tmp_path):
    (tmp_path / "Q001.md").write_text("A")
    (tmp_path / "Q002.md").write_text("B")

    answers = load_answers(str(tmp_path))
    assert answers == ["A", "B"]


def test_run_and_grade():
    client = DummyClient()
    questions = ["q1", "q2"]
    responses = run_benchmark(client, questions)

    assert responses == ["response 1", "response 2"]
    assert client.prompts == questions

    scores = grade(responses, ["a", "b"])
    assert scores == {1: 0.0, 2: 0.0}
