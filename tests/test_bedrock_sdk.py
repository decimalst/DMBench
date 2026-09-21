"""Validate Converse payloads against the real AWS SDK without AWS requests."""

import pytest

import providers


def test_real_bedrock_converse_contract(monkeypatch):
    boto3 = pytest.importorskip("boto3")
    from botocore.stub import Stubber

    # Explicit dummy credentials avoid inspecting local credentials/metadata endpoints.
    session = boto3.Session(
        aws_access_key_id="testing", aws_secret_access_key="testing", region_name="us-east-1"
    )
    monkeypatch.setattr(boto3, "Session", lambda **kwargs: session)
    adapter = providers.BedrockClient("test-model", temperature=0.0, max_tokens=32, timeout=8)
    assert adapter.client.meta.config.retries["total_max_attempts"] == 1
    assert adapter.client.meta.config.read_timeout == 8
    with Stubber(adapter.client) as stubber:
        stubber.add_response(
            "converse",
            {
                "output": {"message": {"role": "assistant", "content": [{"text": "B"}]}},
                "stopReason": "end_turn",
                "usage": {"inputTokens": 10, "outputTokens": 1, "totalTokens": 11},
                "metrics": {"latencyMs": 5},
            },
            {
                "modelId": "test-model",
                "messages": [{"role": "user", "content": [{"text": "Question"}]}],
                "inferenceConfig": {"maxTokens": 32, "temperature": 0.0},
            },
        )
        assert adapter.generate("Question") == "B"
        assert adapter.last_response_metadata["usage"]["totalTokens"] == 11
        stubber.assert_no_pending_responses()
    with Stubber(adapter.client) as stubber:
        stubber.add_client_error(
            "converse",
            service_error_code="AccessDeniedException",
            service_message="SECRET response details",
        )
        with pytest.raises(providers.ProviderError) as exc:
            adapter.generate("Question")
        assert "AccessDeniedException" in str(exc.value)
        assert "SECRET" not in str(exc.value)
        stubber.assert_no_pending_responses()
