#!/bin/bash
set -e

# ==============================================================================
# INITIALIZATION SCRIPT (Bash Wrapper)
# ==============================================================================
# What this does: Executes standard PostgreSQL role and database creation using
# environment variables passed from docker-compose.yml.
# Why this default: Hardcoding passwords in raw .sql files violates secure design.
# Bash interpolation ensures secrets remain strictly in the .env file lifecycle.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
  CREATE ROLE litellm_app WITH LOGIN PASSWORD '${LITELLM_DB_PASSWORD}';
  CREATE ROLE openclaw_app WITH LOGIN PASSWORD '${OPENCLAW_DB_PASSWORD}';

  ALTER ROLE litellm_app CONNECTION LIMIT 100;

  ALTER ROLE openclaw_app SET work_mem = '64MB';
  ALTER ROLE openclaw_app CONNECTION LIMIT 50;

  CREATE DATABASE litellm_db OWNER litellm_app;
  CREATE DATABASE openclaw_db OWNER openclaw_app;

  \c openclaw_db
  CREATE EXTENSION IF NOT EXISTS vector;
  GRANT ALL PRIVILEGES ON SCHEMA public TO openclaw_app;

  \c litellm_db
  GRANT ALL PRIVILEGES ON SCHEMA public TO litellm_app;
EOSQL
