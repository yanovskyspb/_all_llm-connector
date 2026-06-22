-- Stage-based fallback chains for ailenta_parser routes
-- Prerequisite: 005_seed_provider_openrouter_usa.sql

ALTER TABLE llm_routes
  ADD COLUMN stage INT NOT NULL DEFAULT 0
    COMMENT 'Fallback order within (caller_script, function_key, model_slot); 0 = primary';

ALTER TABLE llm_routes
  DROP INDEX uk_llm_route_slot;

ALTER TABLE llm_routes
  ADD UNIQUE KEY uk_llm_route_stage (project_id, caller_script, function_key, model_slot, stage);

SET @proj := (SELECT id FROM llm_projects WHERE code = 'ailenta_parser' LIMIT 1);
SET @or := (SELECT id FROM llm_providers WHERE code = 'openrouter' LIMIT 1);
SET @or_usa := (SELECT id FROM llm_providers WHERE code = 'openrouter_usa' LIMIT 1);
SET @rep := (SELECT id FROM llm_providers WHERE code = 'replicate' LIMIT 1);
SET @rai := (SELECT id FROM llm_providers WHERE code = 'routerai' LIMIT 1);
SET @vsg := (SELECT id FROM llm_providers WHERE code = 'vsegpt' LIMIT 1);

DELETE l FROM llm_request_logs l
INNER JOIN llm_routes r ON r.id = l.route_id
WHERE r.project_id = @proj;

DELETE FROM llm_routes WHERE project_id = @proj;

-- prompt_llm_check.py / default (5-stage chain)
INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, comment
) VALUES
  (@proj, 'prompt_llm_check.py', 'default', 1, 0, @or, 'stepfun/step-3.5-flash:free', 0, 60, 3, 5, 'LLM check: stage 0 openrouter'),
  (@proj, 'prompt_llm_check.py', 'default', 1, 1, @or_usa, 'stepfun/step-3.5-flash:free', 0, 60, 3, 5, 'LLM check: stage 1 openrouter_usa'),
  (@proj, 'prompt_llm_check.py', 'default', 1, 2, @rep, 'stepfun/step-3.5-flash:free', 0, 60, 3, 5, 'LLM check: stage 2 replicate'),
  (@proj, 'prompt_llm_check.py', 'default', 1, 3, @rai, 'stepfun/step-3.5-flash:free', 0, 60, 3, 5, 'LLM check: stage 3 routerai'),
  (@proj, 'prompt_llm_check.py', 'default', 1, 4, @vsg, 'stepfun/step-3.5-flash:free', 0, 60, 3, 5, 'LLM check: stage 4 vsegpt');

-- prompts_pre_list_headers_generate.py / default
INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, response_format, comment
) VALUES
  (@proj, 'prompts_pre_list_headers_generate.py', 'default', 1, 0, @or, 'openai/gpt-5-mini', 0.7, 120, 3, 5, 'json_object', 'Generate headers: stage 0'),
  (@proj, 'prompts_pre_list_headers_generate.py', 'default', 1, 1, @or_usa, 'openai/gpt-5-mini', 0.7, 120, 3, 5, 'json_object', 'Generate headers: stage 1'),
  (@proj, 'prompts_pre_list_headers_generate.py', 'default', 1, 2, @rep, 'openai/gpt-5-mini', 0.7, 120, 3, 5, 'json_object', 'Generate headers: stage 2'),
  (@proj, 'prompts_pre_list_headers_generate.py', 'default', 1, 3, @rai, 'openai/gpt-5-mini', 0.7, 120, 3, 5, 'json_object', 'Generate headers: stage 3'),
  (@proj, 'prompts_pre_list_headers_generate.py', 'default', 1, 4, @vsg, 'openai/gpt-5-mini', 0.7, 120, 3, 5, 'json_object', 'Generate headers: stage 4');

-- prompts_pre_list_translate_ru.py / default
INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, comment
) VALUES
  (@proj, 'prompts_pre_list_translate_ru.py', 'default', 1, 0, @or, 'openai/gpt-5-mini', 0.2, 120, 3, 5, 'Translate: stage 0'),
  (@proj, 'prompts_pre_list_translate_ru.py', 'default', 1, 1, @or_usa, 'openai/gpt-5-mini', 0.2, 120, 3, 5, 'Translate: stage 1'),
  (@proj, 'prompts_pre_list_translate_ru.py', 'default', 1, 2, @rep, 'openai/gpt-5-mini', 0.2, 120, 3, 5, 'Translate: stage 2'),
  (@proj, 'prompts_pre_list_translate_ru.py', 'default', 1, 3, @rai, 'openai/gpt-5-mini', 0.2, 120, 3, 5, 'Translate: stage 3'),
  (@proj, 'prompts_pre_list_translate_ru.py', 'default', 1, 4, @vsg, 'openai/gpt-5-mini', 0.2, 120, 3, 5, 'Translate: stage 4');

-- headers_vote_1 (was model_slot 1)
INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, response_format, comment
) VALUES
  (@proj, 'prompts_pre_list_headers_vote.py', 'headers_vote_1', 1, 0, @or, 'openai/gpt-5-nano', 0, 120, 3, 5, 'json_object', 'Headers vote 1: stage 0'),
  (@proj, 'prompts_pre_list_headers_vote.py', 'headers_vote_1', 1, 1, @or_usa, 'openai/gpt-5-nano', 0, 120, 3, 5, 'json_object', 'Headers vote 1: stage 1'),
  (@proj, 'prompts_pre_list_headers_vote.py', 'headers_vote_1', 1, 2, @rep, 'openai/gpt-5-nano', 0, 120, 3, 5, 'json_object', 'Headers vote 1: stage 2'),
  (@proj, 'prompts_pre_list_headers_vote.py', 'headers_vote_1', 1, 3, @rai, 'openai/gpt-5-nano', 0, 120, 3, 5, 'json_object', 'Headers vote 1: stage 3'),
  (@proj, 'prompts_pre_list_headers_vote.py', 'headers_vote_1', 1, 4, @vsg, 'openai/gpt-5-nano', 0, 120, 3, 5, 'json_object', 'Headers vote 1: stage 4');

-- headers_vote_2 (was model_slot 2)
INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, response_format, comment
) VALUES
  (@proj, 'prompts_pre_list_headers_vote.py', 'headers_vote_2', 1, 0, @or, 'ibm-granite/granite-4.1-8b', 0, 120, 3, 5, 'json_object', 'Headers vote 2: stage 0'),
  (@proj, 'prompts_pre_list_headers_vote.py', 'headers_vote_2', 1, 1, @or_usa, 'ibm-granite/granite-4.1-8b', 0, 120, 3, 5, 'json_object', 'Headers vote 2: stage 1'),
  (@proj, 'prompts_pre_list_headers_vote.py', 'headers_vote_2', 1, 2, @rep, 'ibm-granite/granite-4.1-8b', 0, 120, 3, 5, 'json_object', 'Headers vote 2: stage 2'),
  (@proj, 'prompts_pre_list_headers_vote.py', 'headers_vote_2', 1, 3, @rai, 'ibm-granite/granite-4.1-8b', 0, 120, 3, 5, 'json_object', 'Headers vote 2: stage 3'),
  (@proj, 'prompts_pre_list_headers_vote.py', 'headers_vote_2', 1, 4, @vsg, 'ibm-granite/granite-4.1-8b', 0, 120, 3, 5, 'json_object', 'Headers vote 2: stage 4');

-- prompt_meta_extract.py / extract — exception: openrouter only (2 stages)
INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, max_tokens, comment
) VALUES
  (@proj, 'prompt_meta_extract.py', 'extract', 1, 0, @or, 'z-ai/glm-4.5-air:free', 0, 120, 3, 5, 3001, 'Extract: glm primary'),
  (@proj, 'prompt_meta_extract.py', 'extract', 1, 1, @or, 'openrouter/free', 0, 120, 3, 5, 3001, 'Extract: openrouter/free fallback');

-- Notebooks (5-stage chain each)
INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, sort_order, comment
) VALUES
  (@proj, 'process_articles.ipynb', 'default', 1, 0, @or, 'openai/gpt-4o-mini', 0.7, 180, 3, 5, 10, 'process_articles: stage 0'),
  (@proj, 'process_articles.ipynb', 'default', 1, 1, @or_usa, 'openai/gpt-4o-mini', 0.7, 180, 3, 5, 10, 'process_articles: stage 1'),
  (@proj, 'process_articles.ipynb', 'default', 1, 2, @rep, 'openai/gpt-4o-mini', 0.7, 180, 3, 5, 10, 'process_articles: stage 2'),
  (@proj, 'process_articles.ipynb', 'default', 1, 3, @rai, 'openai/gpt-4o-mini', 0.7, 180, 3, 5, 10, 'process_articles: stage 3'),
  (@proj, 'process_articles.ipynb', 'default', 1, 4, @vsg, 'openai/gpt-4o-mini', 0.7, 180, 3, 5, 10, 'process_articles: stage 4');

INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, sort_order, comment
) VALUES
  (@proj, 'prompts_pre_list_processor.ipynb', 'create', 1, 0, @or, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 20, 'pre_list create: stage 0'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'create', 1, 1, @or_usa, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 20, 'pre_list create: stage 1'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'create', 1, 2, @rep, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 20, 'pre_list create: stage 2'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'create', 1, 3, @rai, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 20, 'pre_list create: stage 3'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'create', 1, 4, @vsg, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 20, 'pre_list create: stage 4');

INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, sort_order, comment
) VALUES
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_1', 1, 0, @or, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 21, 'pre_list optimize: stage 0'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_1', 1, 1, @or_usa, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 21, 'pre_list optimize: stage 1'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_1', 1, 2, @rep, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 21, 'pre_list optimize: stage 2'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_1', 1, 3, @rai, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 21, 'pre_list optimize: stage 3'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_1', 1, 4, @vsg, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 21, 'pre_list optimize: stage 4');

INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, sort_order, comment
) VALUES
  (@proj, 'prompts_pre_list_description.ipynb', 'default', 1, 0, @or, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 30, 'description: stage 0'),
  (@proj, 'prompts_pre_list_description.ipynb', 'default', 1, 1, @or_usa, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 30, 'description: stage 1'),
  (@proj, 'prompts_pre_list_description.ipynb', 'default', 1, 2, @rep, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 30, 'description: stage 2'),
  (@proj, 'prompts_pre_list_description.ipynb', 'default', 1, 3, @rai, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 30, 'description: stage 3'),
  (@proj, 'prompts_pre_list_description.ipynb', 'default', 1, 4, @vsg, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 30, 'description: stage 4');

INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, sort_order, comment
) VALUES
  (@proj, 'prompts_telegram_processor.ipynb', 'default', 1, 0, @or, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 40, 'telegram: stage 0'),
  (@proj, 'prompts_telegram_processor.ipynb', 'default', 1, 1, @or_usa, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 40, 'telegram: stage 1'),
  (@proj, 'prompts_telegram_processor.ipynb', 'default', 1, 2, @rep, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 40, 'telegram: stage 2'),
  (@proj, 'prompts_telegram_processor.ipynb', 'default', 1, 3, @rai, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 40, 'telegram: stage 3'),
  (@proj, 'prompts_telegram_processor.ipynb', 'default', 1, 4, @vsg, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 40, 'telegram: stage 4');

INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, sort_order, comment
) VALUES
  (@proj, 'prompts_pre_list_best_selector.ipynb', 'default', 1, 0, @or, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 50, 'best selector: stage 0'),
  (@proj, 'prompts_pre_list_best_selector.ipynb', 'default', 1, 1, @or_usa, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 50, 'best selector: stage 1'),
  (@proj, 'prompts_pre_list_best_selector.ipynb', 'default', 1, 2, @rep, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 50, 'best selector: stage 2'),
  (@proj, 'prompts_pre_list_best_selector.ipynb', 'default', 1, 3, @rai, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 50, 'best selector: stage 3'),
  (@proj, 'prompts_pre_list_best_selector.ipynb', 'default', 1, 4, @vsg, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 50, 'best selector: stage 4');

INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, sort_order, comment
) VALUES
  (@proj, 'prompt_extractor_tester.ipynb', 'default', 1, 0, @or, 'openai/gpt-4o', 0.7, 300, 3, 5, 60, 'extractor tester: stage 0'),
  (@proj, 'prompt_extractor_tester.ipynb', 'default', 1, 1, @or_usa, 'openai/gpt-4o', 0.7, 300, 3, 5, 60, 'extractor tester: stage 1'),
  (@proj, 'prompt_extractor_tester.ipynb', 'default', 1, 2, @rep, 'openai/gpt-4o', 0.7, 300, 3, 5, 60, 'extractor tester: stage 2'),
  (@proj, 'prompt_extractor_tester.ipynb', 'default', 1, 3, @rai, 'openai/gpt-4o', 0.7, 300, 3, 5, 60, 'extractor tester: stage 3'),
  (@proj, 'prompt_extractor_tester.ipynb', 'default', 1, 4, @vsg, 'openai/gpt-4o', 0.7, 300, 3, 5, 60, 'extractor tester: stage 4');

INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, sort_order, comment
) VALUES
  (@proj, 'articles_maker_results.ipynb', 'default', 1, 0, @or, 'openai/gpt-4o-mini', 0.7, 180, 3, 5, 70, 'articles maker: stage 0'),
  (@proj, 'articles_maker_results.ipynb', 'default', 1, 1, @or_usa, 'openai/gpt-4o-mini', 0.7, 180, 3, 5, 70, 'articles maker: stage 1'),
  (@proj, 'articles_maker_results.ipynb', 'default', 1, 2, @rep, 'openai/gpt-4o-mini', 0.7, 180, 3, 5, 70, 'articles maker: stage 2'),
  (@proj, 'articles_maker_results.ipynb', 'default', 1, 3, @rai, 'openai/gpt-4o-mini', 0.7, 180, 3, 5, 70, 'articles maker: stage 3'),
  (@proj, 'articles_maker_results.ipynb', 'default', 1, 4, @vsg, 'openai/gpt-4o-mini', 0.7, 180, 3, 5, 70, 'articles maker: stage 4');
