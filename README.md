# DMBench

[![Tests and data validation](https://github.com/decimalst/DMBench/actions/workflows/ci.yml/badge.svg)](https://github.com/decimalst/DMBench/actions/workflows/ci.yml)

**A local and hosted model evaluation set for Dungeons & Dragons fifth edition's 2014 rules.**

DMBench asks 100 rules questions through LM Studio, an OpenAI-compatible endpoint (including models hosted on NVIDIA Brev), or AWS Bedrock. It preserves the responses and provides a source-backed answer key for review. Tests and data validation run offline, without a model, account, or API key.

**Dataset version 2.0.0 uses the 2014 rules with official errata, not the 2024 revision.** Q094 explicitly uses the revised Bladesinger feature. The [content audit](docs/CONTENT_AUDIT.md) documents every item: **93 source-verified, 1 interpretive, and 6 provisional pending access to the relevant 2014 book text**. Provisional items cannot receive automatic scores.

## Start here

Python **3.11–3.14** is supported. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest --cov
python benchmark_outline.py --validate-only
```

On Windows, activate with `.venv\Scripts\Activate.ps1` in PowerShell. Validation itself uses only Python's standard library; installing test dependencies is optional if you only want to validate or perform an offline dry run.

Try the complete reporting flow without LM Studio:

```bash
python benchmark_outline.py --dry-run --output-dir reports/offline-demo
```

This writes 100 clearly labeled placeholder responses and a report with **no scores**. Use a new output directory for every run; existing directories are never overwritten.

## Choose a provider

| `--provider` | Connection | Optional dependency |
|---|---|---|
| `lmstudio` (default) | Local LM Studio SDK | `requirements.txt` |
| `brev` | Your Brev-hosted NIM/vLLM chat-completion endpoint | None |
| `openai-compatible` | Any compatible `/chat/completions` endpoint | None |
| `bedrock` | AWS Bedrock Converse API | `requirements-bedrock.txt` |

All providers use the same prompts, question bank, and grading policy. Hosted runs contact your configured service and can incur inference charges. Start with `--limit 1` to check the connection; omit it for all 100 questions. DMBench connects to existing deployments—it does not provision GPU instances or deploy models.

## Run a local model

1. Install [LM Studio](https://lmstudio.ai/), download/load a model, and enable its local server in the Developer tab (or run `lms server start`).
2. Install the separately pinned SDK dependency:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Supply your actual LM Studio model identifier:

   ```bash
   python benchmark_outline.py \
     --model "YOUR_MODEL_IDENTIFIER" \
     --temperature 0 \
     --max-tokens 1024 \
     --output-dir reports/my-model-run-01
   ```

`LM_STUDIO_MODEL` can supply the model identifier instead of `--model`. The SDK uses its default local connection. For a remote LM Studio HTTP server, use `--provider openai-compatible --base-url` instead. See the [SDK documentation](https://lmstudio.ai/docs/python/llm-prediction/chat-completion) for its connection and prediction interfaces.

Every question starts a fresh conversation. Only the edition instruction, question, and answer-format instruction reach the model; the reference answer and audit notes do not. The data is fully validated before model initialization. `--dataset-dir` selects another root with the same 100-item contract; the default bank resolves relative to the script, even if invoked from another working directory.

Use `python benchmark_outline.py --help` for all options. Model downloads and inference are not part of the test suite.

## Run a model hosted on NVIDIA Brev

Deploy a compatible model server on your Brev instance, then forward its API port in a separate terminal:

```bash
brev port-forward my-instance --port 8000:8000
```

Run a one-question smoke test using the model identifier exposed by that server:

```bash
python benchmark_outline.py \
  --provider brev \
  --base-url http://localhost:8000/v1 \
  --model "YOUR_SERVED_MODEL_ID" \
  --limit 1 \
  --output-dir reports/brev-smoke
```

`brev` uses the same adapter as `openai-compatible`; it records Brev as the provider in the report. The server must expose `/chat/completions` under the supplied API root. The [NVIDIA Brev guide](https://docs.nvidia.com/brev/guides/inference-deployment/deploying-nims) documents NIM deployment and recommends port forwarding for API clients; browser-authenticated tunnel links may return a login page or redirect instead of an API response.

For a protected HTTPS endpoint, set its inference bearer token in `DMBENCH_API_KEY` through your environment or secret manager. `--api-key-env MY_PROVIDER_TOKEN` selects another environment variable; its value never appears in CLI arguments or report configuration. Unauthenticated port-forwarded servers need no key. A Brev management or NGC download key is not automatically an inference endpoint credential.

## Run AWS Bedrock

Install the AWS adapter dependency and use your normal AWS credentials (SSO/profile, environment, or workload role):

```bash
python -m pip install -r requirements-bedrock.txt

python benchmark_outline.py \
  --provider bedrock \
  --aws-region us-east-1 \
  --aws-profile research \
  --model "YOUR_CONVERSE_MODEL_OR_INFERENCE_PROFILE_ID" \
  --limit 1 \
  --output-dir reports/bedrock-smoke
```

Omit `--aws-profile` to use the standard credential chain. You need access to the model in the selected region and permission for `bedrock:InvokeModel`. Some models use an inference-profile ID/ARN rather than a bare foundation-model ID. Use a model that supports the [Bedrock Converse API](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html).

Both hosted adapters support `--request-timeout 120` and `--temperature default` to omit the temperature parameter when the selected model requires its own default. OpenAI-compatible servers can select `--token-parameter max_completion_tokens` instead of the default `max_tokens`. Unsupported model parameters fail explicitly; there is no silent parameter change, provider fallback, or automatic inference retry.

[Hosted model setup and troubleshooting](docs/HOSTED_MODELS.md) covers authentication, endpoint formats, partial runs, and report metadata. To test report generation without credentials or network access:

```bash
python benchmark_outline.py --provider bedrock --dry-run --limit 1 --output-dir reports/bedrock-offline
```

## Understand the results

| Section | Items | Automatic treatment |
|---|---:|---|
| Multiple choice | Q001–Q050 | An explicit A–D choice receives 1 or 0; ambiguous or verbose responses need review. |
| Short answers | Q051–Q075 | A listed accepted answer receives 1; other wording needs review rather than being assumed wrong. |
| Scenarios | Q076–Q100 | Always require a reviewer using the reference answer and 0–2 rubric. |

Case, whitespace, and simple Markdown emphasis are normalized. `B`, `B.`, and `Answer: B` are recognized; `A or B`, `not B`, and prose containing an answer letter are not guessed. Short-answer aliases preserve meaningful units, conjunctions, and extra claims. For example, paladin multiclass prerequisites require Strength **and** Charisma; replacing “and” with “or” never receives automatic credit.

The six provisional items are **Q058, Q067, Q068, Q069, Q081, and Q096**. Q088 tests interpretation of a teleportation interaction and has no forced yes/no ruling. Their status is visible in the report and audit.

A run creates:

```text
reports/my-model-run-01/
├── Q001.txt          # Exact raw response, saved immediately
├── ...
├── Q100.txt
└── results.json      # Inputs, references, sources, per-item grades, run metadata
```

The JSON report records the dataset version and SHA-256 fingerprint, exact prompts, requested model identifier, SDK/Python versions where applicable, provider/endpoint or AWS region, generation parameters, timestamps, raw responses, reference answers, and review status. Report schema 2 also records the selected question IDs; `--limit` keeps the full-bank fingerprint while reducing the selected set. Hosted responses include token usage when supplied and a stop reason. Truncated, filtered, or otherwise incomplete hosted completions require review even if their text matches the answer key. Failed or interrupted runs keep completed responses and identify unanswered items. Reports use UTF-8 and are ignored by Git under `report/` and `reports/`.

**`accuracy_on_automatically_scored` is not whole-benchmark accuracy.** It excludes pending responses, scenarios, unrecognized output, and provisional items. In particular, accepted short answers enter this denominator while unrecognized short answers do not: treating that ratio as a leaderboard score would be biased. Review all eligible responses and publish section-specific results, denominators, and grading decisions. Keep provisional items excluded until their sources are checked. The tool does not yet import manual grades or calculate a final human-reviewed score.

Record the exact model file/quantization or hosted model revision, serving software version, and other deployment settings alongside a published run. Temperature zero alone does not guarantee deterministic reproduction. Token limits can truncate answers; inspect the saved text. This small public question bank is not a validated measure of overall DM quality, and models may have seen its questions during training.

## Review and maintain the question bank

The canonical inputs are:

- [`questions/`](questions/): one numbered question per `Q###.md`.
- [`answers/`](answers/): a single letter, short answer, or scenario reference answer with the same ID.
- [`dataset.json`](dataset.json): edition/version, accepted short answers, source locators, review status, audit notes, and rubric levels.

The [question booklet](dnd_benchmark_questions.md), [answer booklet](dnd_benchmark_answers.md), and [audit ledger](docs/CONTENT_AUDIT.md) are generated views of those files. After an edit:

```bash
python manage_dataset.py
python manage_dataset.py --check
ruff check .
ruff format --check .
python -m pytest --cov
```

Use `ruff format .` when formatting needs updating. See [CONTRIBUTING.md](CONTRIBUTING.md) for the review checklist and source policy.

Version 2 corrects numerous incorrect keys and scenario claims, and rewrites ambiguous premises. **Scores are not comparable with the original bank.** Original content remains in Git at `3ce375f`; the audit records which question/answer pairs changed. Automated checks enforce identity, completeness, valid answer options, metadata, known correction regressions, and exact booklet synchronization. They do not independently prove a rules interpretation correct.

## Automation

[GitHub Actions](.github/workflows/ci.yml) runs on pushes and pull requests with Python 3.11, 3.12, 3.13, and 3.14. It checks lint, formatting, data validity, generated documents, tests, a **95% combined line/branch coverage minimum**, and an offline report smoke test. A separate job checks the installed LM Studio SDK and validates Bedrock requests with the real AWS SDK's Stubber. All tests and smoke runs avoid live model services. Coverage and smoke reports are uploaded as artifacts. Dependabot checks Python dependencies and Actions monthly.

Runtime SDKs are separate from development dependencies so normal CI never needs a model or network service. Local mocked runs and SDK contract checks do not establish that a particular model or hosted deployment is available; perform a real run before publishing model results.

## Sources and attribution

The audit uses [SRD 5.1](https://www.dndbeyond.com/attachments/39j2li89/SRD5.1-CCBY4.0License.pdf), the 2014 Basic Rules, official errata, and the Sage Advice Compendium. The source registry distinguishes publicly verified rules from purchase-gated follow-up references. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for SRD attribution.
