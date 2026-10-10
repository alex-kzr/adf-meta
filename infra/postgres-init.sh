#!/usr/bin/env bash
set -euo pipefail
# One-time empty-volume initialization. Values come only from generated secret files.
for name in migrator-password api-db-password checkpoint-db-password; do
  value="$(cat "/run/secrets/$name")"
  [[ "$value" =~ ^[a-f0-9]{64}$ ]] || { echo "Invalid generated database credential" >&2; exit 1; }
done
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set ON_ERROR_STOP=1 \
  --set migrator_password="$(cat /run/secrets/migrator-password)" \
  --set api_password="$(cat /run/secrets/api-db-password)" \
  --set checkpoint_password="$(cat /run/secrets/checkpoint-db-password)" <<'SQL'
CREATE ROLE adf_migrator LOGIN PASSWORD :'migrator_password' NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE ROLE adf_api LOGIN PASSWORD :'api_password' NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE ROLE adf_orchestrator LOGIN PASSWORD :'checkpoint_password' NOSUPERUSER NOCREATEDB NOCREATEROLE;
ALTER DATABASE adf OWNER TO adf_migrator;
REVOKE ALL ON DATABASE adf FROM PUBLIC;
GRANT CONNECT ON DATABASE adf TO adf_api, adf_orchestrator;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
CREATE SCHEMA control AUTHORIZATION adf_migrator;
CREATE SCHEMA runtime AUTHORIZATION adf_migrator;
CREATE SCHEMA audit AUTHORIZATION adf_migrator;
CREATE SCHEMA checkpoints AUTHORIZATION adf_migrator;
GRANT USAGE ON SCHEMA control, runtime, audit TO adf_api;
GRANT USAGE, CREATE ON SCHEMA checkpoints TO adf_orchestrator;
SQL
