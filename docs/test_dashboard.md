# Test Dashboard

Локальная dev-страница для обзора маршрутов LLM и проверки реального `complete()` по скриптам.

## Установка

```bash
pip install -e "C:\cursors\dev\_all_llm-connector[web]"
```

## Переменные окружения

Скопируйте [`.env.example`](../.env.example) в `.env` в корне репозитория и заполните значения.

| Переменная | Назначение |
|------------|------------|
| `LLM_DB_HOST`, `LLM_DB_USER`, `LLM_DB_PASSWORD` | Подключение к `_llm_connector` |
| `API_OPENROUTER_KEY`, `API_VSEGPT_KEY`, `API_ROUTERAI_KEY`, `API_REPLICATE_KEY`, … | Ключи провайдеров |

## Запуск

Из корня репозитория (PowerShell):

```powershell
.\scripts\run_test_dashboard.ps1
```

Или вручную:

```bash
pip install -e ".[web]"
uvicorn scripts.test_dashboard.app:app --host 127.0.0.1 --port 8765 --reload
```

Открыть: http://127.0.0.1:8765

**Важно:** сервер должен быть запущен в отдельном терминале. Если страница не открывается — сначала запустите скрипт выше.

### MySQL (Tailscale)

Хост по умолчанию: **`100.75.41.14`** (MySQL через Tailscale, не HTTP).

При необходимости переопределите в `.env` в корне репозитория:

```
LLM_DB_HOST=100.75.41.14
LLM_DB_USER=root
LLM_DB_PASSWORD=...
```

Без доступной БД HTML откроется, но таблица покажет ошибку подключения.

## API

| Endpoint | Описание |
|----------|----------|
| `GET /` | HTML-таблица |
| `GET /api/projects` | Список проектов |
| `GET /api/routes?project_code=ailenta_parser` | Матрица маршрутов |
| `POST /api/test-script` | Тест всех активных роутов скрипта через `complete()` |

Тело `POST /api/test-script`:

```json
{"project_code": "ailenta_parser", "caller_script": "prompt_meta_extract.py"}
```

## Поведение теста

- Вызывается production `complete()` с сообщением `Reply with exactly: OK`
- Логи пишутся в `llm_request_logs` с `deployment_code=test_dashboard`
- При ошибках возможен рост `failure_count` и suspend роута (как в проде)
- Только localhost, без аутентификации — не для публичного деплоя
