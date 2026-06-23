# -*- coding: utf-8 -*-
from llm_connector.replicate_client import collect_replicate_output, model_predictions_url


def test_model_predictions_url():
    assert (
        model_predictions_url("openai/gpt-5-mini")
        == "https://api.replicate.com/v1/models/openai/gpt-5-mini/predictions"
    )
    assert "stepfun/step-3.5-flash" in model_predictions_url("stepfun/step-3.5-flash:free")


def test_collect_output_list():
    assert collect_replicate_output(["hel", "lo"]) == "hello"
