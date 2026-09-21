# Hosted model runs

DMBench connects to an existing inference service. Provisioning a Brev instance, downloading weights, choosing a GPU, and enabling AWS model access remain deployment tasks. The benchmark does not perform those operations.

## NVIDIA Brev and other compatible endpoints

The `brev` and `openai-compatible` providers send a non-streaming `POST` to `<base-url>/chat/completions`. Each request contains the selected model, a single user message, the requested token limit, and temperature unless omitted. The response must contain exactly one choice with a nonempty text `message.content`. Responses/Completions APIs, streaming, tool execution, multimodal inputs, and arbitrary provider-specific request fields are not supported by this adapter.

For a Brev NIM server listening on port 8000, run this in a separate terminal and keep it running:

```bash
brev port-forward my-instance --port 8000:8000
```

Then run the benchmark against `http://localhost:8000/v1`. Use the model name served by NIM/vLLM, not the Brev instance name. The deployment's `/v1/models` endpoint can list served model IDs. NVIDIA documents the endpoint and forwarding flow in its [NIM deployment guide](https://docs.nvidia.com/brev/guides/inference-deployment/deploying-nims).

For another compatible hosted service:

```bash
python benchmark_outline.py \
  --provider openai-compatible \
  --base-url https://YOUR_API_HOST/v1 \
  --api-key-env MY_INFERENCE_TOKEN \
  --model YOUR_MODEL_ID \
  --temperature 0 \
  --max-tokens 1024 \
  --request-timeout 120 \
  --limit 1 \
  --output-dir reports/hosted-smoke
```

Set `MY_INFERENCE_TOKEN` outside the command, using your shell environment or secret manager. The default variable is `DMBENCH_API_KEY`, and absence of that default variable means no Authorization header. If you explicitly select a custom variable, an unset/empty value fails before any request. The token is used only as the HTTP bearer credential; this adapter does not accept a literal key argument or read `.env` files.

Supply the API **root**, normally ending in `/v1`, rather than the full `/chat/completions` path. HTTPS is required for remote hosts; HTTP is supported on `localhost`, `127.0.0.1`, or `::1` for local serving and port forwarding. URLs containing user credentials, query strings, or fragments are rejected. There is no default paid endpoint and no service fallback.

Brev's browser-authenticated Cloudflare tunnels may return HTML or redirects. Use port forwarding or a direct endpoint configured for API authentication. DMBench rejects redirects rather than forwarding its bearer token to another route or host. Authentication is whatever your **inference server** requires; the Brev management key and NGC image-download credential serve different purposes.

Some compatible services require `max_completion_tokens` instead of `max_tokens`. Select the exact field with `--token-parameter max_completion_tokens`. For a model that disallows an explicit sampling temperature, use `--temperature default`; the request then omits temperature rather than silently substituting a value. Other model-specific request options are not yet exposed.

## AWS Bedrock

Install `requirements-bedrock.txt`. The adapter uses Boto3's standard [credential chain](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html), including named profiles, SSO credentials, environment credentials, and workload roles. It does not require static keys in the benchmark configuration.

```bash
python benchmark_outline.py \
  --provider bedrock \
  --aws-region us-east-1 \
  --aws-profile research \
  --model YOUR_MODEL_OR_INFERENCE_PROFILE_ID \
  --temperature default \
  --max-tokens 1024 \
  --limit 1 \
  --output-dir reports/bedrock-smoke
```

Use an authenticated profile or omit `--aws-profile` for the default chain. An explicit `--aws-region` takes precedence over `AWS_REGION`; otherwise Boto3 resolves its configured region (including `AWS_DEFAULT_REGION` or profile configuration). Model availability and inference profiles are region-specific.

The adapter calls [Converse](https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-runtime/client/converse.html) with `modelId`, one user message containing a text block, and `inferenceConfig`. A model ID or supported inference-profile ID/ARN can be supplied. The principal needs `bedrock:InvokeModel` and access to the chosen model/profile; profile routing may require permissions on destination model resources as well. Models must support Converse and the supplied inference parameters. Prompt-management resource ARNs, model-specific `InvokeModel` payloads, and Bedrock streaming are outside this adapter's scope.

Visible text blocks are joined in their original order. Reasoning blocks are not treated as the model's final answer. Tool-use responses are rejected because DMBench does not run tools for the model. SDK service errors expose a recognized error code and troubleshooting guidance, without writing remote message bodies or SDK exception details into reports.

## Reports, limits, and failures

- `--limit N` selects the first N questions in ID order, after validating the entire 100-item bank. It is a connection/smoke-test facility, not a representative sampling method. Omit it for a full run.
- The report's `dataset_sha256` identifies the full loaded bank, and `selected_ids` identifies what this run attempted. The summary denominator counts selected items only.
- Hosted reports record provider, nonsecret API root or AWS region, requested parameters, available SDK version, and per-response usage/stop reason. API keys, AWS credential objects, authorization headers, and profile configuration are not serialized.
- A normal `stop` (compatible API), `end_turn`, or `stop_sequence` (Bedrock) permits normal grading. Token exhaustion, filtering, guardrails, and unknown stop reasons force manual review; the answer text is still preserved.
- `--request-timeout` defaults to 120 seconds for hosted socket operations. Bedrock uses it for both connect and read timeouts. It is not a wall-clock deadline for the complete 100-question run and does not configure the LM Studio SDK.
- Each hosted question makes one inference attempt. A rate limit, timeout, authentication failure, or malformed response stops the run with a nonzero exit code, retaining completed responses and marking the report failed. There is no automatic retry, checkpoint resume, or model fallback. A timed-out request might still have been processed and billed remotely.
- Choose a new output directory for another attempt. Inspect the saved report before rerunning a full paid benchmark.
- `--dry-run` and `--validate-only` never initialize a hosted SDK, resolve AWS credentials, or send requests. A dry-run report records the selected provider but no active connection configuration and no model scores.

Do not compare smoke-test accuracy with full-run accuracy. For published evaluations, record the exact hosted model revision, region/deployment, token budget, and serving settings along with the saved prompts, fingerprint, and human-review decisions.
