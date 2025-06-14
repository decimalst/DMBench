import os
import argparse
from typing import List, Dict, Optional
try:
    import lmstudio as lms
except ImportError:  # pragma: no cover - optional dependency for tests
    lms = None


class LMStudioClient:
    """Client to interact with local LM Studio models via the lmstudio-python SDK."""

    def __init__(self, model_name: str):
        if lms is None:
            raise ImportError(
                "lmstudio package is required for LMStudioClient but is not installed"
            )
        # Initialize the model using the convenience API
        self.model = lms.llm(model_name)

    def generate(self, prompt: str) -> str:
        """Send prompt to the model and return its response text."""
        result = self.model.respond(prompt)
        # result may be a string or an object with a text attribute
        if isinstance(result, str):
            return result
        # try common attributes for response text
        return getattr(result, 'text', str(result))


def load_questions(path: str) -> List[str]:
    """Load question texts from a directory and append section instructions."""
    files = sorted(f for f in os.listdir(path) if f.endswith('.md'))

    section_i = "Choose the one best answer (A–D)."
    section_ii = "Give a single word, number, or brief phrase."
    section_iii = (
        "Explain what happens according to official rules. A thorough answer "
        "cites page numbers or core-rule sources where possible."
    )

    questions: List[str] = []
    for fname in files:
        with open(os.path.join(path, fname), 'r', encoding='utf-8') as f:
            text = f.read().strip()

        # Determine section by question number in filename, e.g., Q001.md
        try:
            qnum = int(fname[1:4])
        except ValueError:
            qnum = 0

        if 1 <= qnum <= 50:
            text = f"{text}\n\n{section_i}"
        elif 51 <= qnum <= 75:
            text = f"{text}\n\n{section_ii}"
        else:
            text = f"{text}\n\n{section_iii}"

        questions.append(text)
    return questions


def load_answers(path: str) -> List[str]:
    """Load answer texts from a directory."""
    files = sorted(f for f in os.listdir(path) if f.endswith('.md'))
    answers: List[str] = []
    for fname in files:
        with open(os.path.join(path, fname), 'r', encoding='utf-8') as f:
            answers.append(f.read().strip())
    return answers


def run_benchmark(client: LMStudioClient, questions: List[str]) -> List[str]:
    """Query the model for each question, printing progress and responses."""
    responses = []
    total = len(questions)
    bar_width = 20
    for i, prompt in enumerate(questions, start=1):
        resp = client.generate(prompt)
        responses.append(resp)

        filled = int(bar_width * i / total)
        bar = "#" * filled + "-" * (bar_width - filled)
        print(f"[{bar}] {i}/{total}")
        print(resp)
    return responses


def grade(
    responses: List[str],
    answers: List[str],
    output_file: Optional[str] = None,
) -> Dict[int, float]:
    """Placeholder grading logic.

    All responses are written to ``output_file`` if provided so that they can be
    graded by an external model. Each line of the file contains ``Q###:``
    followed by the model's response for that question.
    """

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            for i, resp in enumerate(responses, start=1):
                f.write(f"Q{i:03}: {resp}\n")

    scores: Dict[int, float] = {}
    for i, _ in enumerate(responses, start=1):
        scores[i] = 0.0
    return scores


def main():
    parser = argparse.ArgumentParser(
        description='Run D&D benchmark with LM Studio local models.'
    )
    parser.add_argument(
        '--model', type=str, default=os.environ.get('LM_STUDIO_MODEL', 'qwen/qwen3-32b'),
        help='Name of the local model to load'
    )
    parser.add_argument(
        '--questions-dir', type=str, default='questions',
        help='Path to the directory containing question .md files'
    )
    parser.add_argument(
        '--answers-dir', type=str, default='answers',
        help='Path to the directory containing answer .md files'
    )
    parser.add_argument(
        '--output', type=str, default='responses.txt',
        help='File to write model responses for external grading'
    )
    args = parser.parse_args()

    client = LMStudioClient(args.model)
    questions = load_questions(args.questions_dir)
    answers = load_answers(args.answers_dir)

    print(f"Loaded {len(questions)} questions and {len(answers)} answers.")
    print("Running benchmark...")
    responses = run_benchmark(client, questions)
    scores = grade(responses, answers, args.output)

    print("Results:")
    for idx, score in scores.items():
        print(f"Q{idx:03}: {score}")


if __name__ == '__main__':
    main()
