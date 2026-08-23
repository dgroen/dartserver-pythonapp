# WSO2IS Production Migration Plan (H2 -> PostgreSQL)

## Objective
Migrate production WSO2IS from H2 to PostgreSQL with no data loss, migrate all WSO2 configuration, and make the GitHub Actions deployment process generic for both test and production while keeping production rollout aligned with the test environment flow.

## Status Update (2026-08-22)
Re-verified against current repo/config state:
- Production is confirmed still on H2 (`environments/production/wso2is-config/deployment.toml` in the config repo, `type = "h2"`). Test is already on PostgreSQL, so it remains a valid baseline for Phase 1.
- **Phase 4 (generic GitHub Actions pipeline) is already implemented**, not future work — [.github/workflows/deploy-unified.yml](../.github/workflows/deploy-unified.yml) already has parameterized test/production jobs, a mandatory production approval gate, a `backup-production` job, a `restore-on-failure` job, and a `rollback-production` job. Treat Phase 4 below as done; remaining pipeline work is closing the gap noted below, not building it from scratch.
- **Decided: rollback stays manual, approval-gated — not automatic.** `restore-on-failure` and `rollback-production` sit behind human-approval GitHub Environments (`production-restore-approval`, `production-rollback`), which does not match the original "automatic rollback on failed verification" constraint. Keeping it manual rather than building automatic rollback now: this is a first-ever H2->PostgreSQL cutover for this system, the failure modes are still being discovered (see rehearsal findings below), and an unattended automatic restore of a production identity/auth database carries more risk than a short human-in-the-loop pause. The constraint below has been updated to reflect this as the decided policy, not a placeholder.
- **Phase 2's core deliverable (H2 -> PostgreSQL export/import tooling) has not been started.** No migration-tool script or wrapper exists anywhere in the repo yet. This is the critical path item blocking everything else — nothing in Phases 5-7 can run until this exists and is tested.
- No dry run/rehearsal (Phase 6) has been executed yet.

## Execution Model
- Environment provisioning and the deploy sequence itself run through the existing `deploy-unified.yml` GitHub Actions pipeline (test -> approval gate -> production), reusing its approval gates and backup/restore jobs rather than reimplementing them ad hoc.
- One-time, migration-specific manual actions (e.g. the initial H2 export, PostgreSQL import/verification, any hand-run parity checks) are run remotely over SSH from the operator machine, outside the pipeline.
- SSH access from the operator machine to production is now set up and confirmed working (jumphost `strato.vdi.prd` -> `strato.vdi.prd.dartserver`), via `~/.ssh/config` on that machine plus the `bto` keypair. Not used yet for anything against real production — see rehearsal below.

## Phase 2/6 Local Rehearsal Results (2026-08-23)
Built and ran the missing H2 -> PostgreSQL migration tool end-to-end against an isolated, disposable rehearsal stack (never touching the running dev stack or production):
- `docker-compose-migration-rehearsal.yml` — throwaway H2-backed `wso2is-source`, PostgreSQL `postgres` (official WSO2 DDL from the test config), and PostgreSQL-backed `wso2is-target`.
- `helpers/run_wso2_migration_rehearsal.sh` — orchestrates: seed representative data (reusing `helpers/register_wso2_test_client.py`, `helpers/configure_wso2_redirects.py`, `helpers/test_wso2_provision_user.py`), freeze + back up via `helpers/backup_docker_volumes.sh` (made project-scoped via a `PROJECT_NAME` env override, backward compatible), migrate, start target.
- `helpers/migrate_wso2_h2_to_postgres.sh` — the actual Phase 2 deliverable: reads H2 files **from the backup tarball** (never a live volume, matching the plan's freeze-then-backup cutover sequence), exports every table generically via H2's `CSVWRITE`, loads into PostgreSQL via `\copy` with `session_replication_role = replica` (skips FK ordering), resyncs sequences afterward.
- `helpers/verify_wso2_migration_parity.sh` — row-count diff per table plus functional checks (admin login, seeded users, OAuth token issuance + introspection).

**Result: the migration mechanism works.** 36/39 tables matched exactly on row count, including every auth-relevant table (users, roles, role assignments, OAuth client, service providers, claims, scopes, IdP). All functional checks passed: admin SCIM login, all 3 seeded users present, OAuth token issuance and introspection both succeeded against the migrated PostgreSQL-backed target.

**Three concrete gaps were found, and all three are now fixed and re-verified (2026-08-23, second rehearsal pass):**
1. **Schema drift** — 10 consent-management tables (`CM_PURPOSE`, `CM_RECEIPT`, etc.) exist in WSO2IS 7.1.0's H2 schema but had no matching table in the official Postgres DDL in the config repo. Fixed by [helpers/migration-rehearsal/missing-wso2-identity-tables-postgresql.sql](../helpers/migration-rehearsal/missing-wso2-identity-tables-postgresql.sql) (DDL translated from a live H2 instance's schema, in the same style as the existing DDL). **This file still needs to be merged into `dartserver-config/environments/*/wso2is-config/postgresql-identity.sql` before a real production run** — it's currently only wired into the rehearsal compose file.
2. **BLOB/CLOB CSV encoding gap** — `REG_CONTENT` (a real PNG image, stored as H2 `BINARY LARGE OBJECT`) failed to load entirely: H2's default CSVWRITE stringifies binary content unsafely. Fixed in `helpers/migrate_wso2_h2_to_postgres.sh`'s export step: BLOB/CLOB columns (detected generically per-table from `INFORMATION_SCHEMA.COLUMNS`, matching both the abbreviated and full H2 type names) are now hex-encoded as `\x<hex>`, PostgreSQL's native `bytea` text format, so the existing `\copy` loads them with no special-casing needed. Re-verified: 16/16 rows now match.
3. **Baseline seed-data collisions** — a handful of tables throw PK conflicts because both H2 and the Postgres DDL insert the same default rows independently. Fixed by loading every table through an unconstrained `TEMP` staging table first, then `INSERT ... ON CONFLICT DO NOTHING` into the real table, instead of a raw `\copy` (which would abort the whole table's load, not just the duplicate row, on the first collision). Re-verified: no errors, all rows present.

**Second rehearsal pass result: every table matched exactly except `REG_LOG` (298 vs 307)** — expected, not a defect: the target WSO2IS instance had already been running for several minutes handling its own health checks before verification ran, writing a handful of registry log entries of its own.

Also found and fixed two infra bugs during the rehearsal, worth knowing about since they'd bite anyone else running these tools:
- `helpers/backup_docker_volumes.sh`'s volume-existence prompt wasn't actually gated by `-y`/`--yes` (would hang non-interactively) — fixed.
- `pg_isready` with no `-h` flag checks the local Unix socket, which can report "healthy" while postgres is still mid-initdb on its internal temp server, before the real TCP-listening server is up. The rehearsal compose file's healthcheck now forces `-h 127.0.0.1`; **`docker-compose-wso2.yml` (used by test/production) has the same latent issue and was intentionally left unchanged — still needs the same fix before this tooling is used for real.**
- Spawning one throwaway `docker run` container per table (for both the loader and the row-count verifier) was found to destabilize/slow things badly under host load — once for the target postgres itself (container churn contributed to it being sent an unexpected shutdown mid-load), and separately made verification take 40+ minutes instead of seconds. Both now batch all tables into a single `psql` session per database.

Rehearsal stack was fully torn down after each run (`docker compose down -v` equivalent); nothing from it persists.

## Follow-Up Fixes (2026-08-23, after the second rehearsal pass)
- **DDL merged for real.** The `CM_*` table DDL is now appended to `dartserver-config/environments/test/wso2is-config/postgresql-identity.sql` (not just the rehearsal-only copy), and sanity-checked by loading both `postgresql-shared.sql` and the updated `postgresql-identity.sql` into a scratch PostgreSQL instance end-to-end with no errors. Production doesn't have its own copy of this file yet (still H2) — when production is provisioned for PostgreSQL, it should get this same, now-corrected, test config.
- **Healthcheck race fixed in the real compose file.** `docker-compose-wso2.yml`'s `postgres` healthcheck now uses `pg_isready -h 127.0.0.1 -U postgres` (was socket-only), with a `start_period: 60s` added. `docker-compose-test.yml` inherits it (doesn't redefine the healthcheck). `docker-compose-localhost.yml` (local-dev-only, not part of the test/production deploy path) was left untouched.
- **Rollback policy decided**, see Confirmed Constraints below.

## Real Production Data Validation (2026-08-23)
Validated the migration tool against actual production data (not synthetic seed data), read-only end to end:
- Took a read-only backup of `dartserver-pythonapp_wso2is_data` **on the production host itself**, using the existing unmodified `helpers/backup_docker_volumes.sh` — the exact same mechanism `backup-production` already uses, so nothing new or risky was exercised against production. Production's live containers/data were never touched or modified.
- Pulled only the `wso2is_data.tar.gz` backup down to a local scratchpad (never the repo), ran `helpers/migrate_wso2_h2_to_postgres.sh` unmodified against it into a disposable target, then immediately deleted the production backup copy from the production host and, after the check below, from local disk too.
- **Result: 197/197 tables matched exactly** (137 identity + 60 shared) — including the partial-collision cases (some tables had a mix of pre-existing baseline rows and real data; `ON CONFLICT DO NOTHING` correctly kept only the real duplicates out while inserting everything else). `wso2is-target` booted healthy on the first attempt against this real, migrated data, with no schema errors.
- No new bugs found — every fix from the synthetic rehearsal held up against ~3 months of real production data.
- **Scope note:** verification here was structural only (row counts, target health) — no login, token issuance, or any check that would require real user credentials was attempted, and no actual row content was ever printed to logs. This is validation of the migration mechanism, not the actual production cutover; production's H2 backend is untouched.

**Found but intentionally not touched:** `helpers/restore_docker_volumes.sh` is disconnected from the real pipeline (`deploy-unified.yml`'s `restore-on-failure`/`rollback-production` jobs have their own inline restore logic and don't call it) and is unsafe to run as-is for any kind of isolated test — `stop_containers()` runs bare `docker-compose -f docker-compose-wso2.yml down`, which without project scoping would take down the live `darts-*` dev stack, and `restore_configuration()` overwrites the real `.env`/`nginx`/`deployment.toml` in the repo root. Left unmodified; flagging so nobody runs it expecting it to be safely scoped like `backup_docker_volumes.sh` now is.

## Critical Bug Found and Fixed: WSO2 Schema DDL Was Never Actually Loading (2026-08-23)
While preparing the automated pipeline workflow (below), discovered that the CM_* DDL fix — and in fact the *entire* official WSO2 PostgreSQL DDL — was silently not taking effect through `docker-compose-wso2.yml` (the file test/production actually use):
- `init-postgres-wso2.sql` was recently changed (separately, by the repo owner) to drop the `\c` + `\i` calls that used to load `postgresql-shared.sql`/`postgresql-identity.sql` into the correct `wso2is_shared`/`wso2is_identity` databases, on the assumption WSO2IS's own JDBC auto-provisioning covers everything.
- But `docker-compose-wso2.yml` still mounted those two DDL files directly under `/docker-entrypoint-initdb.d/`, so postgres's own init-script scanner ran them **independently, against the default database** (`dartsdb`) — not `wso2is_shared`/`wso2is_identity`. Verified directly: a fresh instance ended up with `wso2is_identity`/`wso2is_shared` completely schema-less (0 tables from the DDL) and two stray WSO2 tables inside `dartsdb`.
- Also directly confirmed WSO2IS's auto-provisioning **does not** create the `CM_*` tables on its own (0/136 tables on the currently-running, working test instance) — so relying on auto-provisioning alone permanently loses consent-receipt data, independent of the DDL-file bug above.

**Fix:** replaced `init-postgres-wso2.sql` with `init-postgres-wso2.sh` (docker's init system supports conditional shell scripts, not just plain SQL). It creates the three databases, then loads the DDL **only if the schema files are mounted** (`docker-compose-wso2.yml` mounts them under a `wso2-schema/` subdirectory now, so postgres's scanner doesn't also pick them up independently; `docker-compose-localhost.yml` doesn't mount them at all and gets a clear log line explaining it's falling back to auto-provisioning, exactly as before). Verified both paths directly: with the schema mounted, `wso2is_identity` gets all 137 tables (including all 10 `CM_*`) with zero stray tables in `dartsdb`; without it mounted, behavior is unchanged from before (auto-provisioning only, graceful skip logged).

## Pipeline Automation (2026-08-23)
Added `.github/workflows/wso2-migration-rehearsal.yml` — `workflow_dispatch`-only, gated by a new `production-migration-approval` GitHub Environment (needs Required Reviewers configured in GitHub Settings, same as the other approval gates). Reuses the existing `PROD_SERVER_*`/`JUMPHOST_*` secrets and SSH pattern already used by `deploy-unified.yml`'s `deploy-production` job. Automates exactly what was proven manually above: read-only backup on the production host -> download just `wso2is_data.tar.gz` to the runner -> migrate into a disposable `postgres`+`wso2is` pair (from `docker-compose-wso2.yml`, isolated project name, destroyed at job end) -> row-count parity check (`helpers/verify_wso2_migration_row_counts.sh`, new — the row-count-only logic factored out of `helpers/verify_wso2_migration_parity.sh` so both share it) -> WSO2IS health check -> summary -> cleanup (removes the rehearsal backup from production and everything from the runner, `if: always()`).

**Deliberately does not touch `deploy-unified.yml`** — that pipeline auto-runs `deploy-production` on every push to `test`, so embedding a migration step there would need heavy gating to avoid re-running on every routine deploy. This workflow is separate and manual-only. It is also **not the actual production cutover** (that still needs the freeze -> final backup -> migrate -> unfreeze sequence against production's own live `postgres` service, once the team schedules it) — this validates the tool against real data, repeatably, without ever modifying production.

**Not yet done:**
- The workflow has valid YAML and each underlying step's logic was proven individually (backup mechanism against real prod, migrate/verify scripts against a real backup) — but the fully assembled workflow has not been triggered end-to-end yet, since that requires the `production-migration-approval` GitHub Environment to be configured first.
- No restore-from-backup has been exercised even in rehearsal — backups were taken but a simulated-failure recovery was never actually run end-to-end (`helpers/restore_docker_volumes.sh` is unsafe to use for this as-is, see above).

## Confirmed Constraints
- Current production WSO2IS backend: H2
- Acceptable downtime window: up to 30 minutes
- Rollback policy: manual, approval-gated restore/rollback (decided 2026-08-23 — see Status Update above for rationale)
- Configuration source of truth: config repo + GitHub secrets

## Implementation Phases

### 1. Baseline and Parity Definition
- Extract and freeze the exact tested sequence currently used in test:
  - infra startup order
  - schema/bootstrap sequence
  - post-start repair sequence
  - WSO2 baseline validation queries
- Define production parity target: same deployment order and control points as test, unless explicitly documented for production-only infra differences.

### 2. Production H2-to-PostgreSQL Migration Design (Not Started — critical path)
- Build a cutover runbook with explicit freeze and unfreeze points.
- Define export/import mechanism for H2 -> PostgreSQL using official WSO2 migration tooling first, and fallback only if necessary.
- Define migration scope and required parity checks for:
  - users
  - groups and roles
  - service providers
  - OAuth clients/applications
  - claims and claim mappings
  - identity providers
  - redirect/callback/logout URLs

### 3. Backup and Rollback Controls
- Make pre-cutover backup mandatory and blocking.
- Capture:
  - WSO2 runtime/data volumes
  - PostgreSQL volumes/databases
  - relevant config snapshots
- Add integrity checks (artifact existence and non-empty checks at minimum).
- Define automatic rollback triggers:
  - schema validation failure
  - parity check failure
  - health check failure
  - auth smoke test failure
- Implement automatic restore workflow and post-restore health verification.

### 4. Generic GitHub Actions Pipeline (Already Implemented — see Status Update)
- Refactor deployment workflow to parameterize environment (test, production) rather than duplicate logic.
- Parameterize:
  - branch
  - SSH target
  - config bundle path
  - compose file set
  - domain and callback values
  - environment-specific secret names
- Extract reusable logic into shared actions or reusable workflow steps:
  - SSH setup via jumphost
  - config decrypt and bundle
  - remote deploy
  - WSO2 bootstrap and validations
  - backup and restore
- Keep production approval gate as mandatory before production deploy.

### 5. Production Rollout Alignment with Test
- Align production sequence to test sequence:
  1. infra up
  2. schema/bootstrap
  3. WSO2 data/config validation
  4. application services up
- Ensure same non-destructive safety behavior used in test is present in production path.
- Enforce strict mode for production bootstrap/verification.

### 6. Dry Run and Go-Live
- Run a full rehearsal in test or production-like clone with representative data size.
- Measure and optimize total cutover to stay within the 30-minute window.
- Production cutover sequence:
  1. freeze writes
  2. final backup
  3. migrate and bootstrap
  4. verify parity and health
  5. unfreeze
- On any critical failure, auto-rollback and fail deployment.

### 7. Post-Cutover Hardening
- Add post-deploy monitoring for auth/token/introspection endpoints.
- Store migration evidence (counts, checks, timings, backup IDs, rollback status).
- Remove/deprecate H2-dependent run paths and update operations docs.

## Verification Checklist (No-Data-Loss)
1. Pre-flight validation
- Required SQL seeds, config files, and secrets exist for target environment.

2. Backup validation
- Backup artifacts created, non-empty, and retrievable.

3. Data/config parity validation
- Pre/post counts and spot checks pass for users, roles, OAuth apps, service providers, claims, and mappings.

4. Schema validation
- Required WSO2 PostgreSQL tables and baseline seed data present.

5. Runtime validation
- WSO2 health endpoint, app health endpoint, and auth/token/introspection smoke tests succeed.

6. Rollback validation
- Controlled failure test demonstrates automatic rollback and recovery.

7. Idempotency validation
- Re-running bootstrap does not create destructive or duplicate side effects.

## Zero-Downtime Option (If Required)
If zero downtime becomes mandatory, use this section instead of the maintenance-window cutover approach.

### Additional Prerequisites
- Run active-active WSO2IS topology (blue/green or parallel stacks) behind a load balancer with weighted routing.
- Use replicated PostgreSQL (primary + replica) with tested failover.
- Externalize all mutable WSO2 artifacts and secrets so both stacks read the same source of truth.
- Introduce feature flags for write-path control and incremental traffic shifting.

### Zero-Downtime Migration Strategy
1. Build green stack in parallel:
- Provision a new PostgreSQL-backed WSO2IS stack (green) with the same version and config baseline as blue.
- Run schema/bootstrap/repairs on green only.

2. Perform continuous data sync and backfill:
- Export/import baseline H2 data into PostgreSQL.
- Run incremental sync jobs until drift is near-zero.
- Validate users, roles, OAuth apps, claims, and mappings continuously.

3. Execute canary traffic shift:
- Route a small percentage of auth traffic to green.
- Validate login, token issuance, introspection, callback/logout flows.
- Increase traffic gradually only if error rates and latency remain within thresholds.

4. Cutover and stabilize:
- Shift 100 percent traffic to green.
- Keep blue running in hot-standby for rapid failback during stabilization period.

5. Decommission legacy path:
- Stop sync jobs and retire H2 path only after stabilization SLO is met.

### Pipeline Changes Required for Zero Downtime
- Add a dedicated workflow mode (for example ZERO_DOWNTIME=true) in the generic deploy pipeline.
- Add stages for: parallel environment provisioning, sync jobs, canary gates, progressive rollout, and failback orchestration.
- Add automated SLO gates (error rate, auth success ratio, token endpoint latency, introspection latency).
- Keep automatic rollback/failback as a first-class stage, not a manual-only action.

### Zero-Downtime Verification Additions
- Session continuity tests across blue/green (existing sessions and token validity).
- Consistency drift checks at fixed intervals during progressive rollout.
- End-to-end auth journey checks from client login through callback and API authorization.
- Failback rehearsal before production cutover to ensure recovery path meets RTO.

### Risks and Trade-Offs
- Significantly higher implementation and operational complexity.
- Longer preparation timeline due to sync/failover/canary engineering.
- More moving parts in CI/CD, requiring stricter monitoring and on-call readiness.

## Repository Files to Use During Implementation
- .github/workflows/deploy-unified.yml
- helpers/setup-test-environment.sh
- helpers/bootstrap_wso2_test_env.sh
- init-postgres-wso2.sh
- wso2is-7-config/deployment.toml
- docker-compose-wso2.yml
- docker-compose-test.yml
- helpers/backup_docker_volumes.sh
- helpers/restore_docker_volumes.sh
- doc/DEPLOYMENT.md

## Deliverables
- Environment-generic deployment workflow (test + production)
- Production migration runbook with explicit cutover/rollback steps
- Automated parity and health verification scripts wired into CI/CD
- Updated deployment documentation aligned with test rollout model
