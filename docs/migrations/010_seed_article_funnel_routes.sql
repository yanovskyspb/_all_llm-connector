# -*- coding: utf-8 -*-
-- Article funnel routes: process_articles (4-stage) + generate_images (riverflow single stage)
-- Prerequisite: 007_seed_pre_list_funnel_routes.sql

SET @proj := (SELECT id FROM llm_projects WHERE code = 'ailenta_parser' LIMIT 1);
SET @or_usa := (SELECT id FROM llm_providers WHERE code = 'openrouter_usa' LIMIT 1);
SET @rep := (SELECT id FROM llm_providers WHERE code = 'replicate' LIMIT 1);
SET @rai := (SELECT id FROM llm_providers WHERE code = 'routerai' LIMIT 1);
SET @vsg := (SELECT id FROM llm_providers WHERE code = 'vsegpt' LIMIT 1);

-- process_articles.ipynb: replace 5-stage openrouter-first chain with 4-stage USA-first
DELETE l FROM llm_request_logs l
INNER JOIN llm_routes r ON r.id = l.route_id
WHERE r.project_id = @proj
  AND r.caller_script = 'process_articles.ipynb'
  AND r.function_key = 'default';

DELETE FROM llm_routes
WHERE project_id = @proj
  AND caller_script = 'process_articles.ipynb'
  AND function_key = 'default';

INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, response_format, sort_order, comment
) VALUES
  (@proj, 'process_articles.ipynb', 'default', 1, 0, @or_usa, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 'json_object', 10, 'process_articles: stage 0 openrouter_usa'),
  (@proj, 'process_articles.ipynb', 'default', 1, 1, @rep,    'openai/gpt-5-mini', 0.7, 180, 3, 5, 'json_object', 10, 'process_articles: stage 1 replicate'),
  (@proj, 'process_articles.ipynb', 'default', 1, 2, @rai,    'openai/gpt-5-mini', 0.7, 180, 3, 5, 'json_object', 10, 'process_articles: stage 2 routerai'),
  (@proj, 'process_articles.ipynb', 'default', 1, 3, @vsg,    'openai/gpt-5-mini', 0.7, 180, 3, 5, 'json_object', 10, 'process_articles: stage 3 vsegpt');

-- generate_images_for_articles.ipynb: single stage riverflow (no fallback)
DELETE l FROM llm_request_logs l
INNER JOIN llm_routes r ON r.id = l.route_id
WHERE r.project_id = @proj
  AND r.caller_script = 'generate_images_for_articles.ipynb';

DELETE FROM llm_routes
WHERE project_id = @proj
  AND caller_script = 'generate_images_for_articles.ipynb';

INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, sort_order, comment
) VALUES
  (@proj, 'generate_images_for_articles.ipynb', 'default', 1, 0, @or_usa, 'sourceful/riverflow-v2-fast', 0, 600, 3, 5, 11, 'article images: riverflow openrouter_usa only');
