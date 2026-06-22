# -*- coding: utf-8 -*-
import json
from pathlib import Path

from llm_connector.recovery import (
    get_slot_content,
    load_recovery,
    prompt_fingerprint,
    recovery_path,
    write_slot_success,
)


def test_recovery_roundtrip(tmp_path: Path):
    fp = prompt_fingerprint("hello prompt")
    path = recovery_path(str(tmp_path), "ailenta_parser", "vote.py", "headers_vote", "1666")
    write_slot_success(
        path,
        project_code="ailenta_parser",
        caller_script="vote.py",
        function_key="headers_vote",
        entity_id="1666",
        prompt_fingerprint_value=fp,
        model_slot=1,
        provider="openrouter",
        model="m1",
        request_id="r1",
        content='{"ok": true}',
    )
    data = load_recovery(path, fp)
    assert get_slot_content(data, 1) == '{"ok": true}'
    assert path.is_file()
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["slots"]["1"]["status"] == "success"
