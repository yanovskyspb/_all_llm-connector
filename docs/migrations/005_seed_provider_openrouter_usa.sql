-- OpenRouterUSA provider + global provider enable flag
-- Prerequisite: 001_llm_tables.sql

ALTER TABLE llm_providers
  ADD COLUMN is_enabled TINYINT(1) NOT NULL DEFAULT 1
    COMMENT '0 = provider disabled globally; cascade stages are skipped';

INSERT INTO llm_providers (code, base_url, shared_api_key_env, default_verify_ssl, is_enabled) VALUES
  ('openrouter_usa', 'https://openrouter.ai/api/v1', 'API_OPENROUTER_USA_KEY', 1, 1)
ON DUPLICATE KEY UPDATE
  base_url = VALUES(base_url),
  shared_api_key_env = VALUES(shared_api_key_env),
  is_enabled = VALUES(is_enabled);
