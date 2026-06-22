-- Add RouterAI and Replicate providers
-- Prerequisite: 001_llm_tables.sql

DELETE FROM llm_providers WHERE code = 'replit';

INSERT INTO llm_providers (code, base_url, shared_api_key_env, default_verify_ssl, extra_json) VALUES
  ('routerai', 'https://routerai.ru/api/v1', 'API_ROUTERAI_KEY', 1, NULL),
  (
    'replicate',
    'https://openai-proxy.replicate.com/v1',
    'API_REPLICATE_KEY',
    1,
    JSON_OBJECT(
      'note',
      'OpenAI-compatible proxy for Replicate models (owner/name). Native predictions API: https://api.replicate.com/v1'
    )
  )
ON DUPLICATE KEY UPDATE
  base_url = VALUES(base_url),
  shared_api_key_env = VALUES(shared_api_key_env),
  extra_json = VALUES(extra_json);
