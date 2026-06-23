# llm-connector

Shared pip package for LLM routing, request logging, multi-stage fallback, and slot-based recovery.

Development: `C:\cursors\dev\_all_llm-connector`  
GitHub: [yanovskyspb/_all_llm-connector](https://github.com/yanovskyspb/_all_llm-connector)  
Production mirror: `P:\_all_llm-connector` (do not edit directly on `P:\`)

## Install

```bash
pip install -e C:\cursors\dev\_all_llm-connector
```

From a sibling consumer (e.g. `ailenta_parser`) — **use ailenta_parser's venv**, not a separate env in `_all_llm-connector`:

```bash
cd ../ailenta_parser
pip install -e ../_all_llm-connector
# or from GitHub:
pip install "git+https://github.com/yanovskyspb/_all_llm-connector.git"
```

This installs `llm-connector` and its dependencies (`replicate`, `openai`, …) into the consumer environment.

## Database migrations

Dedicated database **`_llm_connector`** (not the consumer app DB):

```bash
python scripts/apply_migrations.py --host 100.75.41.14
```

Env (consumer and migrations):

| Variable | Default |
|----------|---------|
| `LLM_DB_HOST` | `DB_HOST` or **`100.75.41.14`** (Tailscale) |
| `LLM_DB_DATABASE` | **`_llm_connector`** |
| `LLM_DB_USER` / `LLM_DB_PASSWORD` | fall back to `DB_*` |

If `llm_*` tables were created inside `ailenta_parser` by mistake:

```bash
mysql ailenta_parser < docs/migrations/999_drop_from_app_database.sql
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

Copy [`.env.example`](.env.example) to `.env` in **this repo root**. All provider API keys and `LLM_DB_*` are read only from here — consumer apps (e.g. ailenta_parser) do not supply LLM keys from their own `.env`.

| Variable | Purpose |
|----------|---------|
| `API_OPENROUTER_KEY` | Default OpenRouter key (`shared_api_key_env` on provider) |
| `API_OPENROUTER_USA_KEY` | Second OpenRouter account (OpenRouterUSA) |
| `API_VSEGPT_KEY` | VseGPT key |
| `API_ARTEMOX_KEY` | Artemox key |
| `API_OPENAI_KEY` | OpenAI key |
| `API_ROUTERAI_KEY` | [RouterAI](https://routerai.ru/) key |
| `API_REPLICATE_KEY` | [Replicate](https://replicate.com/account/api-tokens) API token (`r8_…`; native Predictions API via `replicate` package) |
| `LLM_DEPLOYMENT_CODE` | Written to `llm_request_logs.deployment_code` (default `internal`) |

Phase 2 (external VPS): see `docs/ARCHITECTURE.md` — Tailscale, replica, outbox.
