-- OpenRouter removed z-ai/glm-4.5-air:free; paid slug is z-ai/glm-4.5-air
UPDATE llm_routes r
JOIN llm_projects p ON p.id = r.project_id
SET r.primary_model = 'z-ai/glm-4.5-air'
WHERE p.code = 'ailenta_parser'
  AND r.caller_script = 'prompt_meta_extract.py'
  AND r.function_key = 'extract'
  AND r.primary_model = 'z-ai/glm-4.5-air:free';
