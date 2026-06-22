-- One-time cleanup: remove llm_* tables mistakenly created in app database.
-- Run against ailenta_parser (or other consumer DB), NOT against _llm_connector.

DROP TABLE IF EXISTS llm_request_logs;
DROP TABLE IF EXISTS llm_routes;
DROP TABLE IF EXISTS llm_providers;
DROP TABLE IF EXISTS llm_projects;
