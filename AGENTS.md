# AGENTS.md

This file tracks project status for the **LLM-powered IaC Drift Reconciliation SaaS**.

## Current Status

- Project is in **scaffold/setup stage**
- Core folders and placeholder entrypoints exist
- No production logic or cloud resources have been fully implemented yet

## Already Implemented

### Repository and Project Skeleton

- Root project folder created: `iac-drift-reconciliation-saas`
- Base files created:
  - `README.md`
  - `pyproject.toml`
  - `.gitignore`
  - `.env.example`

### Documentation Scaffolding

- `docs/architecture.md` placeholder created
- `docs/phases.md` placeholder created

### Infrastructure Scaffolding (Terraform)

- `infra/terraform/README.md` created
- Environment folders created:
  - `infra/terraform/environments/dev`
  - `infra/terraform/environments/staging`
  - `infra/terraform/environments/prod`
- Per-environment placeholder files created:
  - `main.tf`
  - `variables.tf`
  - `outputs.tf`
- Module directories created:
  - `event_ingestion`
  - `processing_inference`
  - `delivery_pr`
  - `control_plane`
  - `observability`
  - `security_iam`

### Backend Service Scaffolding (Python)

- Service directories created:
  - `services/ingestion-filtering`
  - `services/drift-processor`
  - `services/template-validator`
  - `services/pr-delivery`
  - `services/tenant-api`
  - `services/auth`
  - `services/shared`
- Placeholder handlers created in each service:
  - `handler.py` with minimal placeholder return payloads
- Shared package initialized:
  - `services/shared/__init__.py`

### UI Scaffolding (Minimal Dashboard)

- `ui/minimal-dashboard` structure created
- UI folders created:
  - `public`
  - `src/components`
  - `src/pages`
  - `src/services`
- Placeholder UI entrypoint created:
  - `ui/minimal-dashboard/src/main.py`

### Testing and Delivery Scaffolding

- Test directories created:
  - `tests/unit`
  - `tests/integration`
  - `tests/load`
  - `tests/fixtures`
- CI placeholder workflow created:
  - `.github/workflows/ci.yml`
- Script placeholder created:
  - `scripts/bootstrap.sh`

## Not Implemented Yet (To Be Built)

### Phase 1: Foundation and IaC Baseline

- Define Terraform provider, backend state config, and workspace strategy
- Implement reusable Terraform modules for:
  - CloudTrail/S3/SNS/EventBridge/SQS ingestion path
  - Lambda execution roles and least-privilege IAM
  - DynamoDB/S3/Secrets Manager resources
  - API Gateway + Cognito control-plane resources
  - CloudWatch logs, metrics, alarms, and dashboards
- Add per-environment variable wiring and secure secrets references

### Phase 2: Event Ingestion and Drift Signal Pipeline

- Ingest CloudTrail write events and filter resource-modifying actions
- Route filtered events into tenant-partitioned SQS with DLQ
- Add idempotency keys and message dedup strategy
- Add structured event schema and validation

### Phase 3: Drift Processing and LLM Reconciliation

- Implement cross-account AssumeRole flow to fetch current templates
- Build prompt-construction pipeline for CloudTrail event + template context
- Integrate Bedrock inference calls with retries/backoff/quota handling
- Persist intermediate artifacts for auditability

### Phase 4: Template Validation and Retry Loop

- Integrate `cfn-lint` execution in validator service
- Implement iterative correction loop with capped retries
- Produce machine-readable validation reports
- Define reject/failure paths and DLQ escalation

### Phase 5: PR Delivery and CI/CD Integration

- Implement GitHub App auth and token generation
- Create branch/commit/PR workflow with clear commit metadata
- Add PR labels, templates, and reviewer assignment policy
- Emit SNS notifications for success/failure states

### Phase 6: Control Plane API and Tenant Management

- Implement tenant onboarding/offboarding API endpoints
- Implement tenant config persistence in DynamoDB
- Add run history, status, and reconciliation log APIs
- Enforce authn/authz via Cognito and role-based checks

### Phase 7: Minimal Dashboard

- Implement login/session flow (Cognito integration)
- Build tenant setup forms and validation
- Build reconciliation run history list/detail views
- Add basic error states and operational status indicators

### Phase 8: Observability, Testing, and Hardening

- Standardize structured logs and correlation IDs
- Add CloudWatch metrics and alarms across all stages
- Build unit/integration tests for all services
- Implement load tests with Locust and report p50/p95/p99 latency
- Measure and report accuracy/cost/throughput trade-offs
- Add resilience tests (throttling, Bedrock failures, DLQ replay)

## Component Ownership Map (Suggested)

- `services/ingestion-filtering`: Event normalization and queue handoff
- `services/drift-processor`: AssumeRole, template fetch, Bedrock call orchestration
- `services/template-validator`: `cfn-lint`, iterative correction, result emission
- `services/pr-delivery`: GitHub App branch/commit/PR logic
- `services/tenant-api`: Tenant and run-management APIs
- `services/auth`: Cognito/JWT utilities and policy enforcement
- `services/shared`: Shared models, config, logging, retry/idempotency utilities
- `infra/terraform/modules/*`: Reusable deployable AWS infrastructure units
- `ui/minimal-dashboard`: Tenant onboarding and run-monitoring UX

## Definition of Done (Project-Level)

- Drift event to PR flow works end-to-end for a tenant account
- Generated templates pass linting and are reviewable in GitHub PR
- Multi-tenant control plane with authentication and audit trails works
- Observability covers success/failure/latency/cost signals
- Test suite includes unit, integration, and load-test reports

## Immediate Next Steps

- Finalize Terraform backend/state strategy
- Define service contracts (event schema and payload interfaces)
- Implement ingestion-filtering service first, then drift-processor
- Add validator loop before enabling PR delivery in non-dev environments
