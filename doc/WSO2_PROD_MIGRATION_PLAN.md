# WSO2IS Production Migration Plan (H2 -> PostgreSQL)

## Objective
Migrate production WSO2IS from H2 to PostgreSQL with no data loss, migrate all WSO2 configuration, and make the GitHub Actions deployment process generic for both test and production while keeping production rollout aligned with the test environment flow.

## Confirmed Constraints
- Current production WSO2IS backend: H2
- Acceptable downtime window: up to 30 minutes
- Rollback policy: automatic rollback on failed verification
- Configuration source of truth: config repo + GitHub secrets

## Implementation Phases

### 1. Baseline and Parity Definition
- Extract and freeze the exact tested sequence currently used in test:
  - infra startup order
  - schema/bootstrap sequence
  - post-start repair sequence
  - WSO2 baseline validation queries
- Define production parity target: same deployment order and control points as test, unless explicitly documented for production-only infra differences.

### 2. Production H2-to-PostgreSQL Migration Design
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

### 4. Generic GitHub Actions Pipeline
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
- init-postgres-wso2.sql
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
