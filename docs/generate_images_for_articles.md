# generate_images_for_articles.ipynb

Скрипт в проекте **ailenta_parser** (не в `_all_llm-connector`). Маршрут в БД **пока не сидится** — зафиксировано для будущей интеграции с `llm_connector`.

## Планируемый маршрут

| Параметр | Значение |
|----------|----------|
| `project_code` | `ailenta_parser` |
| `caller_script` | `generate_images_for_articles.ipynb` |
| `function_key` | `default` |
| `model_slot` | `1` |

## Цепочка fallback

**Только одна стадия** — модель недоступна на OpenRouter / Replicate / RouterAI.

| stage | provider | model |
|-------|----------|-------|
| 0 | `vsegpt` | `img-stable/stable-diffusion-xl-1024` |

Без stage 1–4 (нет cross-provider chain).

## Env

| Variable | Purpose |
|----------|---------|
| `API_VSEGPT_KEY` | Ключ VseGPT |

## Интеграция (когда будет)

1. Добавить маршрут в `llm_routes` (миграция или seed).
2. Подключить notebook к `complete()` через `llm_connector_bridge`.
3. Убедиться, что `vsegpt.is_enabled = 1` в `llm_providers`.
