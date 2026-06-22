-- Seed: ailenta_parser routes (from legacy llm_settings TZ + current script defaults)
-- Prerequisite: 001_llm_tables.sql

INSERT INTO llm_projects (code, name)
VALUES ('ailenta_parser', 'Ailenta Parser')
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO llm_providers (code, base_url, shared_api_key_env, default_verify_ssl) VALUES
  ('openrouter', 'https://openrouter.ai/api/v1', 'API_OPENROUTER_KEY', 1),
  ('vsegpt', 'https://api.vsegpt.ru/v1/', 'API_VSEGPT_KEY', 1),
  ('artemox', 'https://api.artemox.com/v1', 'API_ARTEMOX_KEY', 1),
  ('openai', 'https://api.openai.com/v1', 'API_OPENAI_KEY', 1),
  ('routerai', 'https://routerai.ru/api/v1', 'API_ROUTERAI_KEY', 1),
  ('replicate', 'https://openai-proxy.replicate.com/v1', 'API_REPLICATE_KEY', 1)
ON DUPLICATE KEY UPDATE
  base_url = VALUES(base_url),
  shared_api_key_env = VALUES(shared_api_key_env);

SET @proj := (SELECT id FROM llm_projects WHERE code = 'ailenta_parser' LIMIT 1);
SET @or := (SELECT id FROM llm_providers WHERE code = 'openrouter' LIMIT 1);

-- pys scripts (legacy TZ section 6)
INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot,
  primary_provider_id, primary_model, temperature, timeout_sec,
  response_format, max_retries, retry_delay_sec, max_tokens, comment
) VALUES
  (@proj, 'prompt_llm_check.py', 'default', 1, @or, 'stepfun/step-3.5-flash:free', 0, 60, NULL, 3, 5, NULL,
   'LLM check for prompt quality'),
  (@proj, 'prompts_pre_list_headers_generate.py', 'default', 1, @or, 'openai/gpt-5-mini', 0.7, 120, 'json_object', 3, 5, NULL,
   'Generate 5 headers'),
  (@proj, 'prompts_pre_list_translate_ru.py', 'default', 1, @or, 'openai/gpt-5-mini', 0.2, 120, NULL, 3, 5, NULL,
   'Translate pre-list to RU'),
  (@proj, 'prompts_pre_list_headers_vote.py', 'headers_vote', 1, @or, 'openai/gpt-5-nano', 0, 120, 'json_object', 3, 5, NULL,
   'Headers vote model 1'),
  (@proj, 'prompts_pre_list_headers_vote.py', 'headers_vote', 2, @or, 'ibm-granite/granite-4.1-8b', 0, 120, 'json_object', 3, 5, NULL,
   'Headers vote model 2'),
  (@proj, 'prompt_meta_extract.py', 'extract', 1, @or, 'z-ai/glm-4.5-air', 0, 120, NULL, 3, 5, 3001,
   'Extract prompt from telegram raw')
ON DUPLICATE KEY UPDATE
  primary_model = VALUES(primary_model),
  temperature = VALUES(temperature),
  timeout_sec = VALUES(timeout_sec),
  response_format = VALUES(response_format),
  max_tokens = VALUES(max_tokens),
  comment = VALUES(comment);

-- ipynb inventory (placeholders — tune models per notebook)
INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, sort_order, comment
) VALUES
  (@proj, 'process_articles.ipynb', 'default', 1, @or, 'openai/gpt-4o-mini', 0.7, 180, 3, 5, 10, 'Notebook: process_articles'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'create', 1, @or, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 20, 'Notebook: pre_list create'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_1', 1, @or, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 21, 'Notebook: pre_list optimize'),
  (@proj, 'prompts_pre_list_description.ipynb', 'default', 1, @or, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 30, 'Notebook: description'),
  (@proj, 'prompts_telegram_processor.ipynb', 'default', 1, @or, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 40, 'Notebook: telegram processor'),
  (@proj, 'prompts_pre_list_best_selector.ipynb', 'default', 1, @or, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 50, 'Notebook: best selector'),
  (@proj, 'prompt_extractor_tester.ipynb', 'default', 1, @or, 'openai/gpt-4o', 0.7, 300, 3, 5, 60, 'Notebook: extractor tester'),
  (@proj, 'articles_maker_results.ipynb', 'default', 1, @or, 'openai/gpt-4o-mini', 0.7, 180, 3, 5, 70, 'Notebook: articles maker')
ON DUPLICATE KEY UPDATE
  primary_model = VALUES(primary_model),
  temperature = VALUES(temperature),
  comment = VALUES(comment);
