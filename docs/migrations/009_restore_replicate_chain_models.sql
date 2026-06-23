-- Revert erroneous 008: replicate stages must keep the same model slug as stage 0
-- (e.g. openai/gpt-5-mini — valid on Replicate: https://replicate.com/openai/gpt-5-mini).
-- Prerequisite: 006_stage_fallback_chains.sql

UPDATE llm_routes r_rep
JOIN llm_providers p ON p.id = r_rep.primary_provider_id AND p.code = 'replicate'
JOIN llm_routes r0
  ON r0.project_id = r_rep.project_id
 AND r0.caller_script = r_rep.caller_script
 AND r0.function_key = r_rep.function_key
 AND r0.model_slot = r_rep.model_slot
 AND r0.stage = 0
SET r_rep.primary_model = r0.primary_model;
