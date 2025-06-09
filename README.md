# DMBench

This repository contains a simple benchmark for measuring LLM performance on Dungeons & Dragons 5e rules questions. The dataset is provided as Markdown files under `questions/` and `answers/`.

`benchmark_outline.py` demonstrates how to load these files and interact with a local model managed through LM Studio. The provided `LMStudioClient` class is a placeholder and should be implemented with the [`lmstudio-python`](https://pypi.org/project/lmstudio/) SDK.

## Requirements

Install dependencies with pip:

```bash
pip install -r requirements.txt
```

`lmstudio` is required for the real benchmark while `pytest` is used for running the unit tests.

## Running the Benchmark

First make sure you have downloaded a model for LM Studio. For example:

```bash
lms get llama-3.2-1b-instruct
```

Set any necessary environment variables (for example `LM_STUDIO_URL` and `LM_STUDIO_TOKEN`) and run:

```bash
python benchmark_outline.py
```

The script loads all questions, queries the model, and prints placeholder scores. Implement `LMStudioClient.generate` and `grade` to perform real evaluations.

## Tests

Unit tests use mock clients instead of LM Studio. Run them with:

```bash
pytest
```
