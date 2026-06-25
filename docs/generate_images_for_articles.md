# generate_images_for_articles.ipynb

Скрипт в проекте **ailenta_parser**. Маршрут в БД `_llm_connector`, вызов через `complete_image()` / `llm_connector_bridge.complete_image_prompt()`.

## Маршрут

| Параметр | Значение |
|----------|----------|
| `project_code` | `ailenta_parser` |
| `caller_script` | `generate_images_for_articles.ipynb` |
| `function_key` | `default` |
| `model_slot` | `1` |

## Цепочка fallback

**Одна стадия** (без cross-provider fallback).

| stage | provider | model | timeout_sec |
|-------|----------|-------|-------------|
| 0 | `openrouter_usa` | `sourceful/riverflow-v2-fast` | 600 |

Параметры изображения для `sourceful/*`: `resolution=1K`, `aspect_ratio=16:9`.

## Env

| Variable | Purpose |
|----------|---------|
| `API_OPENROUTER_USA_KEY` | Ключ OpenRouter USA |

## Интеграция

1. Миграция: `docs/migrations/010_seed_article_funnel_routes.sql`
2. Потребитель: `pys/article_image_generator.py` → `llm_connector_bridge.complete_image_prompt()`
3. Notebook: `ipynb/generate_images_for_articles.ipynb` — `assert_routes_available()` при старте
