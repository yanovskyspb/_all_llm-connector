-- Create dedicated database for llm_connector (run without USE / against server)
CREATE DATABASE IF NOT EXISTS _llm_connector
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
