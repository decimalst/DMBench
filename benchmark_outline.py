"""Outline for running D&D benchmark using local models via LM Studio."""

import os
from typing import List, Dict


class LMStudioClient:
    """Placeholder client to interact with local LM Studio models."""

    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token
        # TODO: implement actual API initialization

    def generate(self, prompt: str) -> str:
        """Send prompt to the model and return its response.

        This method should be implemented using LM Studio's API.
        """
        raise NotImplementedError


def load_questions(path: str) -> List[str]:
    """Load question texts from a directory and append section instructions."""
    files = sorted(f for f in os.listdir(path) if f.endswith(".md"))

    section_i = "Choose the one best answer (A–D)."
    section_ii = "Give a single word, number, or brief phrase."
    section_iii = (
        "Explain what happens according to official rules. A thorough answer "
        "cites page numbers or core-rule sources where possible."
    )

    questions = []
    for fname in files:
        with open(os.path.join(path, fname), "r") as f:
            text = f.read().strip()

        # Determine section by question number.
        qnum = int(fname[1:4])
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
    files = sorted(f for f in os.listdir(path) if f.endswith(".md"))
    answers = []
    for fname in files:
        with open(os.path.join(path, fname), "r") as f:
            answers.append(f.read().strip())
    return answers


def run_benchmark(client: LMStudioClient, questions: List[str]) -> List[str]:
    """Query the model for each question and collect responses."""
    responses = []
    for prompt in questions:
        responses.append(client.generate(prompt))
    return responses


def grade(responses: List[str], answers: List[str]) -> Dict[int, float]:
    """Placeholder grading logic.

    Multiple choice and short answers could be graded automatically.
    Open-ended questions might need manual review.
    """
    scores = {}
    for i, (resp, ans) in enumerate(zip(responses, answers), start=1):
        # TODO: implement real scoring logic
        scores[i] = 0.0
    return scores


def main():
    # Example usage; replace with argument parsing as needed
    url = os.environ.get("LM_STUDIO_URL")
    token = os.environ.get("LM_STUDIO_TOKEN")

    client = LMStudioClient(url, token)
    questions = load_questions("questions")
    answers = load_answers("answers")

    responses = run_benchmark(client, questions)
    scores = grade(responses, answers)

    for idx, score in scores.items():
        print(f"Q{idx:03}: {score}")


if __name__ == "__main__":
    main()
