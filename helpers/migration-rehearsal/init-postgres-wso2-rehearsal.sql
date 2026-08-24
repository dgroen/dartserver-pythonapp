-- Rehearsal-only init script for postgres-target.
-- Creates the two WSO2 databases and loads the same official WSO2 PostgreSQL
-- DDL already used successfully by the test environment
-- (dartserver-config/environments/test/wso2is-config/), mounted here as
-- 02-/03- so docker-entrypoint-initdb.d picks them up in order.
CREATE DATABASE wso2is_shared WITH ENCODING 'UTF8';
CREATE DATABASE wso2is_identity WITH ENCODING 'UTF8';

\c wso2is_shared
\i /docker-entrypoint-initdb.d/02-wso2-shared-postgresql.sql

\c wso2is_identity
\i /docker-entrypoint-initdb.d/03-wso2-identity-postgresql.sql
\i /docker-entrypoint-initdb.d/04-missing-wso2-identity-tables.sql
