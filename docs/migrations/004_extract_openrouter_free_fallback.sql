-- prompt_meta_extract: primary glm (may 404) -> same-provider fallback openrouter/free
UPDATE llm_routes r
JOIN llm_projects p ON p.id = r.project_id
SET
  r.same_provider_fallback_model = 'openrouter/free',
  r.comment = 'Extract: glm:free primary, openrouter/free fallback',
  r.failure_count = 0,
  r.is_suspended = 0,
  r.suspended_at = NULL,
  r.suspend_reason = NULL
WHERE p.code = 'ailenta_parser'
  AND r.caller_script = 'prompt_meta_extract.py'
  AND r.function_key = 'extract';
