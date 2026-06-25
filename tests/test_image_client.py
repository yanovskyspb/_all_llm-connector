# -*- coding: utf-8 -*-
from llm_connector.image_client import openrouter_image_payload


def test_riverflow_payload():
    payload = openrouter_image_payload("sourceful/riverflow-v2-fast", "test prompt")
    assert payload["model"] == "sourceful/riverflow-v2-fast"
    assert payload["prompt"] == "test prompt"
    assert payload["resolution"] == "1K"
    assert payload["aspect_ratio"] == "16:9"
    assert payload["n"] == 1


def test_flux_payload_uses_size():
    payload = openrouter_image_payload("black-forest-labs/flux.2-pro", "x")
    assert payload["size"] == "1344x768"
    assert payload["output_format"] == "png"
