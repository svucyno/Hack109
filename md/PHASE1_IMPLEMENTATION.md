# Phase 1: Backend Foundation - Implementation Notes

## Completed (April 5, 2026)

### 1. Stack Pinning to SRS/PRD Binding
**File**: [pyproject.toml](../pyproject.toml)
- Locked Python to 3.12+ (SRS requirement)
- Django 5.1.3 (matching SRS requirement for Django 5.x)
- Added DRF 3.14.0 for REST API scaffold
- Added djangorestframework-simplejwt 5.3.2 (JWT auth per SRS FR-7.6)
- Added django-cors-headers 4.3.1 (CORS for React SPA per SRS FR-7.7)
- Added psycopg2-binary (PostgreSQL adapter per SRS requirement)
- Added pgvector 0.3.0 (semantic search vectors per SRS 3.3)
- Added celery 5.3.4 (async worker for ingestion pipeline per SRS NFR-5.1)
- Added redis 5.0.1 (Celery broker)
- Using `uv` for dependency management (user preference)

### 2. Django Settings (Production-Safe Baseline)
**File**: [GetHired/settings.py](../GetHired/settings.py)
- Secret key managed via environment variable (not hardcoded)
- DEBUG controlled via environment (safe by default)
- PostgreSQL database configuration with environment variables
- DRF configuration with URL path versioning (SRS FR-7.1)
- JWT authentication using djangorestframework-simplejwt (SRS FR-7.6)
- CORS allowlist for Vite dev server (SRS FR-7.7)
- Celery async worker configuration (SRS NFR-5.1)
- JSON structured logging with correlation IDs (SRS NFR-5.4)
- Security headers enforced (HTTPS, HSTS, secure cookies per SRS NFR-2.5)
- Split-Data Config dictionary for governance parameters

### 3. Canonical Data Models (SRS 3.1: Split-Data Architecture)
**File**: [core/models.py](../core/models.py)

**PrimaryProfile** (Primary Store - SRS FR-3.1)
- Stores encrypted raw resume + PII metadata
- Bound to user_id (UUID)
- resume_blob_uri: External storage reference (S3/Azure Blob)
- pii_json_encrypted: AES-256 encrypted PII entities (SRS NFR-2.1)
- encryption_key_version: KMS key tracking (SRS NFR-2.2)

**ReferenceProfile** (Reference Store - SRS FR-4.1)
- De-identified profile JSON with NO PII by design (SRS NFR-3.4)
- Embedding vector (pgvector) for semantic ranking (SRS 3.3)
- result_status: pending → processed → failed → blocked
- score_normalized ∈ [0, 1] (SRS FR-4.2)
- score_bucket ∈ {1..5} (SRS FR-4.3)
- explanation_json: Evidence snippets + missing skills (SRS FR-4.4)
- model_version + embedding_version tracking (SRS 3.3: Re-embedding contract)

**MappingTable** (Trust Boundary - SRS FR-3.2, FR-3.3)
- Maps reference_no ↔ user_id
- ONE-TO-ONE relationship (SRS FR-3.2: exactly one mapping per profile)
- Only component that bridges AI-facing and identity stores
- Reintegration Service exclusively uses this for de-anonymization

**AuditLog** (Immutable Event Trail - SRS FR-6.3, NFR-3.3)
- event_type: split_created, pii_redacted, scoring_complete, deanonymize_*, score_override, model_changed
- actor_id + actor_role (RBAC tracking per SRS FR-6.1)
- Mandatory reason field for sensitive ops (SRS FR-6.2)
- correlation_id: Trace ID for request correlation (SRS NFR-5.1)
- Retention: 6-12 months configurable (SRS NFR-3.3)
- Immutable after creation (no updates allowed)

### 4. Service Layer Scaffold
**Directories created**:
- core/: Canonical models, custom exception handler, JSON logging
- ingestion/: Resume parsing and OCR pipeline (Phase 2)
- privacy/: PII redaction and validation (Phase 2)
- matching/: Semantic ranking and recommendations (Phase 3)
- governance/: De-anonymization and policy controls (Phase 4)

**AppConfig files registered** in Django INSTALLED_APPS (settings.py)

### 5. DRF and Security Infrastructure
**File**: [core/exceptions.py](../core/exceptions.py)
- Custom exception handler returning standardized error schema (SRS FR-7.5)
- Error format: `{"error": {"code": "...", "message": "...", "details": {...}}}`

**File**: [core/logging.py](../core/logging.py)
- JSONFormatter for structured logging with correlation_id (SRS NFR-5.4)
- Emits JSON logs to stdout for containerized deployments

### 6. API Routing Scaffold
**File**: [GetHired/urls.py](../GetHired/urls.py)
- JWT token endpoints: `/api/v1/auth/token/` and `/api/v1/auth/token/refresh/` (SRS FR-7.6)
- Placeholder routes for Phase 2-5 endpoints (SRS FR-7.1 versioning)
- Comments show endpoint structure per SRS requirements

### 7. Environment Configuration
**File**: [.env.example](./.env.example)
- Template for all required environment variables
- Database, Redis, JWT, CORS, split-data config params
- User should copy to `.env` and populate for local development

## Architecture Decisions (SRS-Compliant)

### Data Isolation (Trust Boundary)
- ✅ Primary_Profile and Reference_Profile in separate logical stores
- ✅ Mapping_Table as only bridge (no AI direct access to PII)
- ✅ PII leakage validation required before Reference_Profile creation
- ⚠️ **Note**: Physical separation (different databases) not yet configured; 
  recommend implementing at deployment time via separate schemas or PostgreSQL roles

### Security Posture
- ✅ SECRET_KEY from environment (not in code)
- ✅ DEBUG=False by default
- ✅ HTTPS redirect + HSTS headers when DEBUG=False
- ✅ Secure session/CSRF cookies
- ✅ PostgreSQL (not SQLite) for production-grade concurrency
- ⚠️ **TODO**: Implement KMS integration for encryption_key_version rotation

### Async Pipeline
- ✅ Celery + Redis configured (SRS NFR-5.1: Async ingestion targets)
- ⚠️ **TODO**: Implement task definitions (extract, OCR, PII, embedding jobs)

### Observability
- ✅ JSON structured logging configured
- ✅ correlation_id field in AuditLog schema
- ⚠️ **TODO**: Implement correlation_id propagation middleware

## Next Steps (Phase 2-5)

### Phase 2: Ingestion Pipeline
- Resume upload endpoint (FR-1.1)
- PDF/DOCX extraction (FR-1.2)
- OCR fallback for scanned PDFs (FR-1.2)
- Structured parsing output (FR-1.3)

### Phase 3: Privacy Guard
- PII detection via Presidio + NER (FR-2.1)
- Redaction and de-identification (FR-2.2)
- Redaction report generation (FR-2.3)
- Fail-closed PII leakage validation (FR-2.4)

### Phase 4: Matching and Recommendations
- Vector embedding generation (SRS 3.3 contract)
- Cosine similarity scoring (FR-4.1)
- Score normalization to [0, 1] (FR-4.2)
- Score bucket mapping 1..5 (FR-4.3)
- Explanation JSON with evidence (FR-4.4)
- Student role recommendations (FR-5.1-5.3)

### Phase 5: Governance and De-anonymization
- De-anonymization policy enforcement (FR-6.1-6.4)
- Mandatory reason capture (FR-6.2)
- Audit event logging (FR-6.3)
- Approval workflow (optional policy mode: FR-6.4)

### Database Migrations
- Run `python manage.py makemigrations core ingestion privacy matching governance`
- Run `python manage.py migrate`
- Enable pgvector extension: `CREATE EXTENSION IF NOT EXISTS vector;`

## SRS Requirement Traceability

| Requirement | Status | Location |
| --- | --- | --- |
| FR-1.x (Ingestion) | Phase 2 | ingestion/ |
| FR-2.x (Privacy Guard) | Phase 2 | privacy/ |
| FR-3.x (Split Storage) | ✅ Done | core/models.py |
| FR-4.x (ATS Scoring) | Phase 3 | matching/ |
| FR-5.x (Recommendations) | Phase 3 | matching/ |
| FR-6.x (De-anonymization) | Phase 4 | governance/ |
| FR-7.x (API Behavior) | ✅ In Progress | GetHired/urls.py, settings.py |
| FR-8.x (Frontend) | Blocked | forntend/ (typo: fix folder name) |
| NFR-2.x (Security) | ✅ Baseline | settings.py |
| NFR-3.x (Privacy/Compliance) | ✅ Schema Ready | core/models.py |
| NFR-4.x (Scalability) | ✅ Architecture | core/models.py (pgvector abstraction) |
| NFR-5.x (Reliability/Observability) | ✅ In Progress | core/logging.py, Celery config |

## Bad Architecture Avoidance Checklist

- ✅ Split storage: PII and de-identified profiles WILL NOT merge
- ✅ Trust boundary: AI services CANNOT query PrimaryProfile directly
- ✅ Versioning: All endpoints MUST be under /api/v1
- ✅ Anonymity: Recruiter views MUST use reference_no (not user_id)
- ✅ Vector contracts: Mismatched embedding_version WILL fail
- ✅ De-anonymization: REQUIRES role + reason + audit log
- ✅ Database: PostgreSQL + pgvector (not SQLite)
- ✅ Async: OCR/PII/embedding WILL run async (not sync in request path)
