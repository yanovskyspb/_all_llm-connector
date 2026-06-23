-- Pre-list funnel: optimize_2..8 (processor) + voter_1..3 (best_selector)
-- Prerequisite: 006_stage_fallback_chains.sql

SET @proj := (SELECT id FROM llm_projects WHERE code = 'ailenta_parser' LIMIT 1);
SET @or := (SELECT id FROM llm_providers WHERE code = 'openrouter' LIMIT 1);
SET @or_usa := (SELECT id FROM llm_providers WHERE code = 'openrouter_usa' LIMIT 1);
SET @rep := (SELECT id FROM llm_providers WHERE code = 'replicate' LIMIT 1);
SET @rai := (SELECT id FROM llm_providers WHERE code = 'routerai' LIMIT 1);
SET @vsg := (SELECT id FROM llm_providers WHERE code = 'vsegpt' LIMIT 1);

-- Remove legacy best_selector single-model default (replaced by voter_1..3)
DELETE l FROM llm_request_logs l
INNER JOIN llm_routes r ON r.id = l.route_id
WHERE r.project_id = @proj
  AND r.caller_script = 'prompts_pre_list_best_selector.ipynb'
  AND r.function_key = 'default';

DELETE FROM llm_routes
WHERE project_id = @proj
  AND caller_script = 'prompts_pre_list_best_selector.ipynb'
  AND function_key = 'default';

-- prompts_pre_list_processor.ipynb / optimize_2 (openai/gpt-5.2)
INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, sort_order, comment
) VALUES
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_2', 1, 0, @or,     'openai/gpt-5.2', 0.7, 180, 3, 5, 22, 'optimize_2: stage 0'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_2', 1, 1, @or_usa, 'openai/gpt-5.2', 0.7, 180, 3, 5, 22, 'optimize_2: stage 1'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_2', 1, 2, @rep,    'openai/gpt-5.2', 0.7, 180, 3, 5, 22, 'optimize_2: stage 2'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_2', 1, 3, @rai,    'openai/gpt-5.2', 0.7, 180, 3, 5, 22, 'optimize_2: stage 3'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_2', 1, 4, @vsg,    'openai/gpt-5.2', 0.7, 180, 3, 5, 22, 'optimize_2: stage 4');

-- optimize_3 (anthropic/claude-sonnet-4.6)
INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, sort_order, comment
) VALUES
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_3', 1, 0, @or,     'anthropic/claude-sonnet-4.6', 0.7, 180, 3, 5, 23, 'optimize_3: stage 0'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_3', 1, 1, @or_usa, 'anthropic/claude-sonnet-4.6', 0.7, 180, 3, 5, 23, 'optimize_3: stage 1'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_3', 1, 2, @rep,    'anthropic/claude-sonnet-4.6', 0.7, 180, 3, 5, 23, 'optimize_3: stage 2'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_3', 1, 3, @rai,    'anthropic/claude-sonnet-4.6', 0.7, 180, 3, 5, 23, 'optimize_3: stage 3'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_3', 1, 4, @vsg,    'anthropic/claude-sonnet-4.6', 0.7, 180, 3, 5, 23, 'optimize_3: stage 4');

-- optimize_4 (anthropic/claude-opus-4.6)
INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, sort_order, comment
) VALUES
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_4', 1, 0, @or,     'anthropic/claude-opus-4.6', 0.7, 180, 3, 5, 24, 'optimize_4: stage 0'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_4', 1, 1, @or_usa, 'anthropic/claude-opus-4.6', 0.7, 180, 3, 5, 24, 'optimize_4: stage 1'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_4', 1, 2, @rep,    'anthropic/claude-opus-4.6', 0.7, 180, 3, 5, 24, 'optimize_4: stage 2'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_4', 1, 3, @rai,    'anthropic/claude-opus-4.6', 0.7, 180, 3, 5, 24, 'optimize_4: stage 3'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_4', 1, 4, @vsg,    'anthropic/claude-opus-4.6', 0.7, 180, 3, 5, 24, 'optimize_4: stage 4');

-- optimize_5 (google/gemini-2.5-pro)
INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, sort_order, comment
) VALUES
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_5', 1, 0, @or,     'google/gemini-2.5-pro', 0.7, 180, 3, 5, 25, 'optimize_5: stage 0'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_5', 1, 1, @or_usa, 'google/gemini-2.5-pro', 0.7, 180, 3, 5, 25, 'optimize_5: stage 1'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_5', 1, 2, @rep,    'google/gemini-2.5-pro', 0.7, 180, 3, 5, 25, 'optimize_5: stage 2'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_5', 1, 3, @rai,    'google/gemini-2.5-pro', 0.7, 180, 3, 5, 25, 'optimize_5: stage 3'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_5', 1, 4, @vsg,    'google/gemini-2.5-pro', 0.7, 180, 3, 5, 25, 'optimize_5: stage 4');

-- optimize_6 (google/gemini-3-flash-preview)
INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, sort_order, comment
) VALUES
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_6', 1, 0, @or,     'google/gemini-3-flash-preview', 0.7, 180, 3, 5, 26, 'optimize_6: stage 0'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_6', 1, 1, @or_usa, 'google/gemini-3-flash-preview', 0.7, 180, 3, 5, 26, 'optimize_6: stage 1'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_6', 1, 2, @rep,    'google/gemini-3-flash-preview', 0.7, 180, 3, 5, 26, 'optimize_6: stage 2'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_6', 1, 3, @rai,    'google/gemini-3-flash-preview', 0.7, 180, 3, 5, 26, 'optimize_6: stage 3'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_6', 1, 4, @vsg,    'google/gemini-3-flash-preview', 0.7, 180, 3, 5, 26, 'optimize_6: stage 4');

-- optimize_7 (google/gemini-3.1-pro-preview)
INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, sort_order, comment
) VALUES
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_7', 1, 0, @or,     'google/gemini-3.1-pro-preview', 0.7, 180, 3, 5, 27, 'optimize_7: stage 0'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_7', 1, 1, @or_usa, 'google/gemini-3.1-pro-preview', 0.7, 180, 3, 5, 27, 'optimize_7: stage 1'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_7', 1, 2, @rep,    'google/gemini-3.1-pro-preview', 0.7, 180, 3, 5, 27, 'optimize_7: stage 2'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_7', 1, 3, @rai,    'google/gemini-3.1-pro-preview', 0.7, 180, 3, 5, 27, 'optimize_7: stage 3'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_7', 1, 4, @vsg,    'google/gemini-3.1-pro-preview', 0.7, 180, 3, 5, 27, 'optimize_7: stage 4');

-- optimize_8 (stepfun/step-3.5-flash:free)
INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, sort_order, comment
) VALUES
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_8', 1, 0, @or,     'stepfun/step-3.5-flash:free', 0.7, 180, 3, 5, 28, 'optimize_8: stage 0'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_8', 1, 1, @or_usa, 'stepfun/step-3.5-flash:free', 0.7, 180, 3, 5, 28, 'optimize_8: stage 1'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_8', 1, 2, @rep,    'stepfun/step-3.5-flash:free', 0.7, 180, 3, 5, 28, 'optimize_8: stage 2'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_8', 1, 3, @rai,    'stepfun/step-3.5-flash:free', 0.7, 180, 3, 5, 28, 'optimize_8: stage 3'),
  (@proj, 'prompts_pre_list_processor.ipynb', 'optimize_8', 1, 4, @vsg,    'stepfun/step-3.5-flash:free', 0.7, 180, 3, 5, 28, 'optimize_8: stage 4');

-- prompts_pre_list_best_selector.ipynb / voter_1 (anthropic/claude-sonnet-4.6)
INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, sort_order, comment
) VALUES
  (@proj, 'prompts_pre_list_best_selector.ipynb', 'voter_1', 1, 0, @or,     'anthropic/claude-sonnet-4.6', 0.7, 180, 3, 5, 50, 'voter_1: stage 0'),
  (@proj, 'prompts_pre_list_best_selector.ipynb', 'voter_1', 1, 1, @or_usa, 'anthropic/claude-sonnet-4.6', 0.7, 180, 3, 5, 50, 'voter_1: stage 1'),
  (@proj, 'prompts_pre_list_best_selector.ipynb', 'voter_1', 1, 2, @rep,    'anthropic/claude-sonnet-4.6', 0.7, 180, 3, 5, 50, 'voter_1: stage 2'),
  (@proj, 'prompts_pre_list_best_selector.ipynb', 'voter_1', 1, 3, @rai,    'anthropic/claude-sonnet-4.6', 0.7, 180, 3, 5, 50, 'voter_1: stage 3'),
  (@proj, 'prompts_pre_list_best_selector.ipynb', 'voter_1', 1, 4, @vsg,    'anthropic/claude-sonnet-4.6', 0.7, 180, 3, 5, 50, 'voter_1: stage 4');

-- voter_2 (openai/gpt-5-mini)
INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, sort_order, comment
) VALUES
  (@proj, 'prompts_pre_list_best_selector.ipynb', 'voter_2', 1, 0, @or,     'openai/gpt-5-mini', 0.7, 180, 3, 5, 51, 'voter_2: stage 0'),
  (@proj, 'prompts_pre_list_best_selector.ipynb', 'voter_2', 1, 1, @or_usa, 'openai/gpt-5-mini', 0.7, 180, 3, 5, 51, 'voter_2: stage 1'),
  (@proj, 'prompts_pre_list_best_selector.ipynb', 'voter_2', 1, 2, @rep,    'openai/gpt-5-mini', 0.7, 180, 3, 5, 51, 'voter_2: stage 2'),
  (@proj, 'prompts_pre_list_best_selector.ipynb', 'voter_2', 1, 3, @rai,    'openai/gpt-5-mini', 0.7, 180, 3, 5, 51, 'voter_2: stage 3'),
  (@proj, 'prompts_pre_list_best_selector.ipynb', 'voter_2', 1, 4, @vsg,    'openai/gpt-5-mini', 0.7, 180, 3, 5, 51, 'voter_2: stage 4');

-- voter_3 (openai/gpt-5.2)
INSERT INTO llm_routes (
  project_id, caller_script, function_key, model_slot, stage,
  primary_provider_id, primary_model, temperature, timeout_sec,
  max_retries, retry_delay_sec, sort_order, comment
) VALUES
  (@proj, 'prompts_pre_list_best_selector.ipynb', 'voter_3', 1, 0, @or,     'openai/gpt-5.2', 0.7, 180, 3, 5, 52, 'voter_3: stage 0'),
  (@proj, 'prompts_pre_list_best_selector.ipynb', 'voter_3', 1, 1, @or_usa, 'openai/gpt-5.2', 0.7, 180, 3, 5, 52, 'voter_3: stage 1'),
  (@proj, 'prompts_pre_list_best_selector.ipynb', 'voter_3', 1, 2, @rep,    'openai/gpt-5.2', 0.7, 180, 3, 5, 52, 'voter_3: stage 2'),
  (@proj, 'prompts_pre_list_best_selector.ipynb', 'voter_3', 1, 3, @rai,    'openai/gpt-5.2', 0.7, 180, 3, 5, 52, 'voter_3: stage 3'),
  (@proj, 'prompts_pre_list_best_selector.ipynb', 'voter_3', 1, 4, @vsg,    'openai/gpt-5.2', 0.7, 180, 3, 5, 52, 'voter_3: stage 4');
