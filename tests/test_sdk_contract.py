"""Exercise the installed SDK's actual text result, without a running server."""

import inspect

import pytest


def test_installed_sdk_contract():
    lms = pytest.importorskip("lmstudio")
    # These are public SDK types; no network/model is accessed.
    assert callable(lms.llm)
    assert "config" in inspect.signature(lms.LLM.respond).parameters
    text = "Actual SDK response text"
    result = lms.PredictionResult(
        content=text,
        parsed=text,
        stats=None,
        model_info=None,
        load_config=None,
        prediction_config=None,
    )
    assert str(result) == text
