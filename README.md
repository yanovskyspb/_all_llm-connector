# llm-connector

Shared pip package for LLM routing, request logging, multi-stage fallback, and slot-based recovery.

Development: `C:\cursors\dev\_all_llm-connector`  
Production mirror: `P:\_all_llm-connector` (do not edit directly on `P:\`)

## Install

```bash
pip install -e C:\cursors\dev\_all_llm-connector
```

From a sibling consumer (e.g. `ailenta_parser`):

```bash
pip install -e ../_all_llm-connector
```

## Database migrations

Run once on the target MySQL database:

```bash
mysql -u root ailenta_parser < docs/migrations/001_llm_tables.sql
mysql -u root ailenta_parser < docs/migrations/002_seed_ailenta_parser.sql
```

## Quick start

```python
import db_connection  # consumer app
from llm_connector import complete, MysqlLlmAdapter

adapter = MysqlLlmAdapter()
cur = db_connection.get_cursor()
result = complete(
    adapter,
    cur,
    project_code="ailenta_parser",
    caller_script="prompt_meta_extract.py",
    function_key="extract",
    messages=[{"role": "user", "content": "..."}],
    entity_id="123",
    recovery_root="runtime/llm_recovery",
)
print(result.content)
```

## Environment

| Variable | Purpose |
|----------|---------|
| `API_OPENROUTER_KEY` | Default OpenRouter key (`shared_api_key_env` on provider) |
| `API_VSEGPT_KEY` | VseGPT key |
| `API_ARTEMOX_KEY` | Artemox key |
| `API_OPENAI_KEY` | OpenAI key |
| `LLM_DEPLOYMENT_CODE` | Written to `llm_request_logs.deployment_code` (default `internal`) |

Phase 2 (external VPS): see `docs/ARCHITECTURE.md` — Tailscale, replica, outbox.
