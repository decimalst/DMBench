# Contributing

Keep changes scoped to the **2014 rules with official errata**. A later feature revision must be named in its question and source metadata. Do not silently update answers to the 2024 rules.

## Change a question or answer

1. Read the primary rule, including exceptions and relevant errata. Record its URL and a precise section/page locator in `dataset.json`. An inaccessible source or forum quotation is not primary-source verification.
2. Edit the matching `questions/Q###.md` and `answers/Q###.md`. Preserve IDs; each multiple-choice item must have exactly four options and exactly one correct answer. Spell out assumptions that affect the outcome.
3. Update the item's `audit_note`, `change`, `review_status`, and accepted answers or scenario rubric. `change` describes the cumulative difference from the dataset's `baseline_commit`. `verified` means the relevant primary rules were inspected; `provisional` means verification is outstanding; `interpretation` means explicit rules still leave the asked-for ruling open.
4. Keep unresolved items provisional and out of scoring. For Q058/Q067/Q068/Q069/Q081/Q096, check the specific 2014 PHB/DMG sections listed in the audit before promoting them. Do not mark them verified merely to make a check pass.
5. For scenario grading, state the required facts in the reference answer. Apply rubric 0 for an incorrect central rule, 1 for a correct but materially incomplete explanation, and 2 for a complete explanation without contradictory claims. Accept equivalent language and defensible interpretations where flagged; exact citations are useful but fabricated citations are not evidence.
6. Bump `dataset_version` when questions, keys, assumptions, or grading policy change. Record the review date; changing the rules edition is a new dataset version, not an invisible maintenance edit.
7. Regenerate the booklets and audit with `python manage_dataset.py`. Never edit generated files directly.

## Validate a change

```bash
python -m pip install -r requirements-dev.txt
ruff check .
ruff format --check .
python benchmark_outline.py --validate-only
python manage_dataset.py --check
python -m pytest --cov
python benchmark_outline.py --dry-run --output-dir reports/contribution-check
```

Use a fresh output directory for each run. Tests use fake clients; no LM Studio download, credentials, or inference are required. Install `requirements.txt` and `requirements-bedrock.txt` to also exercise the real SDKs' offline contracts. Hosted provider tests must never require credentials, provision infrastructure, or call a billable endpoint. Keep the coverage gate at 95% or higher, and add tests for meaningful behavior and known regressions rather than merely increasing the number of assertions.

When evaluating a model, preserve raw responses, state the exact dataset fingerprint and model/settings, and keep manual grading decisions separate from the original report. Report section-specific denominators. Automatically accepted short answers alone cannot establish short-answer accuracy.

## Add or change a provider

Adapters expose `generate(prompt) -> str`. Each call must send a fresh conversation containing only that prompt. Optional `last_response_metadata` records sanitized usage and stop reason, and sets `requires_review` when the completion is not known to be complete. Reset this metadata before each request so a failed request cannot reuse an earlier response's metadata.

Preserve the requested inference parameters, enforce timeouts, and avoid implicit inference retries or provider fallback. Record nonsecret provider configuration in the report. Convert service errors to `ProviderError` without including response bodies, credential values, or SDK exception strings. For HTTP endpoints, do not forward authorization through redirects. Tests should cover payload contracts, rejected configuration, response parsing, failures, report metadata, and offline operation. Use AWS Stubber for SDK schema checks; use test doubles for ordinary CI.
