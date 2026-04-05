# Software Requirements Specification (SRS): AI Talent and Career Ecosystem
Date: April 5, 2026
Version: 1.1
Status: MVP Build-Ready

## 0. Technology Profile (Binding for MVP)
Backend profile:
- Python 3.12+
- Django 5.x
- Django REST Framework (DRF) for REST APIs

Frontend profile:
- React 18+
- Vite 5+ for build and development server

Database profile:
- PostgreSQL 16+ with pgvector extension

All functional and non-functional requirements in this SRS are scoped to this stack unless explicitly marked as post-MVP.

## 1. Introduction
### 1.1 Purpose
This SRS defines functional and non-functional requirements for a dual-domain AI system serving:
- HR recruitment workflows (anonymous ranking, explainable evaluation)
- Student career development workflows (path recommendation, skill-gap closure)

The system uses a split-data architecture to separate personally identifiable information (PII) from AI evaluation inputs.

### 1.2 Scope
Major modules:
1. Privacy Guard: PII detection and redaction.
2. Resume Parser: structured extraction from unstructured resumes.
3. Split Storage Layer: primary and reference stores with mapping table.
4. AI Matching Engine: embedding generation and similarity ranking.
5. Recommendation Engine: career paths and skill-gap outputs.
6. Reintegration Agent: controlled join of AI outputs back to user context.
7. Governance Layer: de-anonymization policy, logging, fairness reporting.

### 1.3 Definitions
- PII: Personally identifiable information.
- Reference_No: System-generated identifier used by AI-facing records.
- DIR: Disparate Impact Ratio.
- Blind Evaluation: AI scoring path without identity fields.

## 2. System Architecture
### 2.1 Split-Data Flow
1. User uploads resume.
2. Parser extracts text (OCR fallback when needed).
3. Privacy Guard identifies and redacts PII.
4. Primary store persists encrypted raw resume + identity metadata.
5. Reference store persists de-identified profile + embedding vectors.
6. Scoring service evaluates reference data against job vectors.
7. Reintegration agent joins by mapping table and publishes results.

### 2.2 Trust Boundaries
1. AI services cannot query primary store directly.
2. Reintegration service is the only component allowed to resolve Reference_No to User_ID.
3. De-anonymization API requires recruiter role and policy checks.

### 2.3 Runtime Components for Selected Stack
1. Django API service:
- Hosts all /api/v1 endpoints.
- Implements RBAC, validation, and orchestration of parser/privacy/matching modules.

2. Django async worker:
- Runs ingestion, OCR, PII pass, and embedding/index jobs asynchronously.
- Uses queue-backed retry with idempotency keys.

3. React + Vite client:
- Serves recruiter/student/admin dashboards.
- Consumes only versioned Django APIs.
- Enforces role-based route guards and de-anonymization confirmation flows.

## 3. Data Model and Contracts
### 3.1 Canonical Tables (MVP)
1. Primary_Profile
- user_id (UUID, PK)
- resume_blob_uri (TEXT)
- pii_json_encrypted (BYTEA/TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

2. Reference_Profile
- reference_no (UUID, PK)
- profile_json (JSONB, de-identified)
- embedding_vector (VECTOR)
- result_status (VARCHAR)
- score_normalized (NUMERIC)
- score_bucket (SMALLINT, 1..5)
- explanation_json (JSONB)
- model_version (VARCHAR)
- embedding_version (VARCHAR)
- updated_at (TIMESTAMP)

3. Mapping_Table
- reference_no (UUID, PK/FK to Reference_Profile)
- user_id (UUID, FK to Primary_Profile)
- created_at (TIMESTAMP)

4. Audit_Log
- event_id (UUID, PK)
- actor_id (UUID or service principal)
- actor_role (VARCHAR)
- event_type (VARCHAR)
- reference_no (UUID, nullable)
- user_id (UUID, nullable)
- reason (TEXT, required for de-anonymize and override)
- event_payload (JSONB)
- created_at (TIMESTAMP)

### 3.2 PII Redaction Contract
PII entities to remove or mask:
- PERSON
- EMAIL_ADDRESS
- PHONE_NUMBER
- LOCATION
- URL
- ORG (optional policy-controlled)
- UNIVERSITY_NAME (optional prestige-bias policy)

Any unresolved high-confidence PII entities above policy threshold block downstream scoring.

### 3.3 Embedding Contract
1. Supported models (MVP):
- text-embedding-3-small
- all-MiniLM-L6-v2

2. Requirements:
- Every vector record must store model_version and embedding_version.
- Re-embedding job required for model_version changes.
- Similarity scoring must not compare vectors from mismatched embedding_version.

## 4. Functional Requirements
### 4.1 Ingestion and Parsing
- FR-1.1: System shall accept PDF and DOCX uploads.
- FR-1.2: System shall run OCR on scanned PDFs when text extraction confidence is below threshold.
- FR-1.3: System shall output a structured parse with skills, roles, years of experience, projects, education.

### 4.2 Privacy Guard
- FR-2.1: System shall detect PII using Presidio and/or transformer NER fallback.
- FR-2.2: System shall redact PII before creating reference profile.
- FR-2.3: System shall store redaction report with entity counts and confidence summary.
- FR-2.4: System shall fail closed if PII leakage validation fails.

### 4.3 Split Storage and Mapping
- FR-3.1: System shall persist raw and de-identified artifacts separately.
- FR-3.2: System shall create exactly one mapping record for each reference profile.
- FR-3.3: System shall enforce referential integrity between mapping and both profile tables.

### 4.4 ATS Scoring and Explanation
- FR-4.1: System shall compute cosine similarity over de-identified vectors only.
- FR-4.2: System shall output score_normalized in [0,1].
- FR-4.3: System shall map normalized score to score_bucket 1..5 by configured thresholds.
- FR-4.4: System shall generate explanation_json with evidence snippets and missing skills.
- FR-4.5: System shall not include candidate identity in explanation output sent to recruiter list view.

### 4.5 Student Recommendations
- FR-5.1: System shall return 3 to 5 recommended career paths with confidence values.
- FR-5.2: System shall produce skill gap list relative to selected target role.
- FR-5.3: System shall provide course recommendations from supported providers with URL, duration, and level.

### 4.6 De-anonymization and Override
- FR-6.1: System shall allow de-anonymization only to authorized recruiter roles.
- FR-6.2: System shall require mandatory reason text for each de-anonymization request.
- FR-6.3: System shall log all de-anonymization and score override events in Audit_Log.
- FR-6.4: System shall support policy mode where manager approval is required before revealing identity.

### 4.7 API Behavior (MVP)
- FR-7.1: API shall expose versioned REST endpoints under /api/v1.
- FR-7.2: Endpoint GET /candidates/{reference_no}/score shall return de-identified scoring payload.
- FR-7.3: Endpoint POST /candidates/{reference_no}/deanonymize shall enforce FR-6 policy checks.
- FR-7.4: Endpoint GET /students/{user_id}/recommendations shall return role paths, gaps, and courses.
- FR-7.5: All API endpoints shall be implemented in DRF and emit JSON responses with standardized error schema.
- FR-7.6: API authentication shall support django-allauth headless session tokens for SPA clients.
- FR-7.7: API shall enforce CORS allowlist for approved frontend origins.

### 4.8 Frontend Requirements (React + Vite)
- FR-8.1: Frontend shall be a React SPA built with Vite and served as static assets in production.
- FR-8.2: Frontend shall consume only /api/v1 endpoints and shall not directly access databases or model services.
- FR-8.3: Recruiter candidate list view shall render anonymized profiles by default.
- FR-8.4: De-anonymization UI shall require reason input and explicit confirmation before API submission.
- FR-8.5: Student dashboard shall display role recommendations, skill gaps, and course links with loading and error states.
- FR-8.6: Frontend shall support responsive layouts for desktop and mobile viewport widths.

## 5. Non-Functional Requirements
### 5.1 Performance
Synchronous request p95 targets:
- Auth and profile fetch <= 50 ms
- Vector retrieval <= 120 ms
- Explanation assembly <= 150 ms
- Reintegration join <= 120 ms
- End-to-end recommendation response <= 500 ms (pre-embedded candidate)

Asynchronous ingestion targets:
- Extraction + OCR <= 1200 ms
- PII pass <= 1200 ms
- Embedding + indexing <= 1000 ms
- Total <= 3400 ms

### 5.2 Security
- NFR-2.1: Data at rest shall use AES-256 encryption.
- NFR-2.2: Encryption keys shall be managed via KMS and rotated at least every 90 days.
- NFR-2.3: Data in transit shall use TLS 1.2 or higher.
- NFR-2.4: Service-to-service access shall use least privilege identities.
- NFR-2.5: Django security middleware shall enforce secure headers, CSRF protections where applicable, and strict session/token settings.
- NFR-2.6: Frontend build shall not expose secrets; runtime configuration shall be injected through environment-safe variables.

### 5.3 Privacy and Compliance
- NFR-3.1: Blind evaluation mode shall be default for all recruiter candidate lists.
- NFR-3.2: Every AI-assisted rejection path shall provide explanation payload for transparency.
- NFR-3.3: Audit logs shall retain split, score, de-anonymize, and override events for at least 6 months.
- NFR-3.4: No PII fields shall be present in reference store by design and by test.

### 5.4 Scalability and Portability
- NFR-4.1: Architecture shall isolate vector retrieval behind service interface to support pgvector to Qdrant migration.
- NFR-4.2: Query filters (experience, degree, skill tags) shall be supported in vector retrieval API.
- NFR-4.3: System shall support at least 5 million profiles on PostgreSQL + pgvector in MVP configuration.

### 5.5 Reliability and Observability
- NFR-5.1: System shall emit trace IDs for ingestion, scoring, and reintegration flows.
- NFR-5.2: Error budget and SLO dashboards shall be available for API latency and scoring failures.
- NFR-5.3: Failed async jobs shall be retried with idempotency keys.
- NFR-5.4: Django APIs and workers shall emit structured logs with correlation_id fields.
- NFR-5.5: Frontend shall capture client-side error telemetry for failed API interactions and rendering failures.

## 6. Fairness and Model Governance
### 6.1 Measurement Policy
- Weekly automated fairness report by monitored cohort.
- Monthly governance review with documented outcomes.

### 6.2 Threshold Policy
- DIR >= 0.80: pass.
- 0.70 <= DIR < 0.80: warning and mandatory mitigation plan.
- DIR < 0.70: fail and release gate for model changes.

### 6.3 Model Change Controls
- Every model/embedding change shall run pre-production regression on:
- ranking correlation
- PII leakage
- fairness metrics
- latency budgets

- Rollback path shall exist for prior model_version.

## 7. Verification and Acceptance Criteria
### 7.1 Test Categories
1. PII leakage tests:
- Assert zero prohibited PII entities in reference profile snapshots.

2. Ranking quality tests:
- Correlation with expert recruiter labels >= 0.87 on benchmark set.

3. Latency tests:
- p95 recommendation API <= 500 ms for pre-embedded workload.

4. Fairness tests:
- DIR policy enforcement and report generation.

5. Governance tests:
- De-anonymization requires role + reason and emits immutable audit entry.

### 7.2 Requirement Traceability
Each FR/NFR shall map to:
- owning service
- automated test suite id
- dashboard metric id
- release gate status

### 7.3 Requirement Traceability Matrix
| Requirement ID | Owning Service | API Endpoint | Data Tables | Test Suite ID | Metric ID | Release Gate |
| --- | --- | --- | --- | --- | --- | --- |
| FR-1.1 | Ingestion Service | POST /api/v1/resumes/upload | Primary_Profile, Mapping_Table | TS-ING-001 | M-ING-UPLOAD-SUCCESS | MVP-BLOCKER |
| FR-1.2 | Parser Service | POST /api/v1/resumes/{reference_no}/parse | Primary_Profile, Reference_Profile | TS-PARSE-002 | M-PARSE-OCR-FALLBACK-RATE | MVP-BLOCKER |
| FR-1.3 | Parser Service | POST /api/v1/resumes/{reference_no}/parse | Reference_Profile | TS-PARSE-003 | M-PARSE-STRUCTURED-FIELD-COVERAGE | MVP-BLOCKER |
| FR-2.1 | Privacy Guard Service | POST /api/v1/privacy/redact | Reference_Profile | TS-PII-001 | M-PII-DETECTION-RECALL | MVP-BLOCKER |
| FR-2.2 | Privacy Guard Service | POST /api/v1/privacy/redact | Reference_Profile | TS-PII-002 | M-PII-REDACTION-SUCCESS | MVP-BLOCKER |
| FR-2.3 | Privacy Guard Service | GET /api/v1/privacy/{reference_no}/report | Audit_Log | TS-PII-003 | M-PII-REPORT-COVERAGE | MVP-BLOCKER |
| FR-2.4 | Privacy Guard Service | POST /api/v1/privacy/validate | Reference_Profile, Audit_Log | TS-PII-004 | M-PII-LEAKAGE-CRITICAL | MVP-BLOCKER |
| FR-3.1 | Storage Service | POST /api/v1/profiles/split-store | Primary_Profile, Reference_Profile | TS-STO-001 | M-SPLIT-WRITE-SUCCESS | MVP-BLOCKER |
| FR-3.2 | Storage Service | POST /api/v1/profiles/split-store | Mapping_Table | TS-STO-002 | M-MAPPING-UNIQUENESS-VIOLATIONS | MVP-BLOCKER |
| FR-3.3 | Storage Service | POST /api/v1/profiles/split-store | Primary_Profile, Reference_Profile, Mapping_Table | TS-STO-003 | M-REF-INTEGRITY-ERROR-RATE | MVP-BLOCKER |
| FR-4.1 | Matching Service | POST /api/v1/candidates/{reference_no}/score | Reference_Profile | TS-MATCH-001 | M-SCORE-BLIND-EVAL-COMPLIANCE | MVP-BLOCKER |
| FR-4.2 | Matching Service | POST /api/v1/candidates/{reference_no}/score | Reference_Profile | TS-MATCH-002 | M-SCORE-NORMALIZATION-VALIDITY | MVP-BLOCKER |
| FR-4.3 | Matching Service | POST /api/v1/candidates/{reference_no}/score | Reference_Profile | TS-MATCH-003 | M-SCORE-BUCKET-CONSISTENCY | MVP-BLOCKER |
| FR-4.4 | Explainability Service | GET /api/v1/candidates/{reference_no}/score | Reference_Profile | TS-EXP-001 | M-EXPL-EVIDENCE-COVERAGE | MVP-BLOCKER |
| FR-4.5 | Explainability Service | GET /api/v1/candidates/{reference_no}/score | Reference_Profile | TS-EXP-002 | M-EXPL-IDENTITY-LEAKAGE | MVP-BLOCKER |
| FR-5.1 | Recommendation Service | GET /api/v1/students/{user_id}/recommendations | Reference_Profile | TS-REC-001 | M-REC-PATH-COUNT-COMPLIANCE | MVP-BLOCKER |
| FR-5.2 | Recommendation Service | GET /api/v1/students/{user_id}/recommendations | Reference_Profile | TS-REC-002 | M-REC-GAP-COVERAGE | MVP-BLOCKER |
| FR-5.3 | Course Adapter Service | GET /api/v1/students/{user_id}/recommendations | Reference_Profile, Audit_Log | TS-REC-003 | M-REC-COURSE-LINK-VALIDITY | MVP-BLOCKER |
| FR-6.1 | Governance Service | POST /api/v1/candidates/{reference_no}/deanonymize | Mapping_Table, Audit_Log | TS-GOV-001 | M-GOV-RBAC-DENY-RATE | MVP-BLOCKER |
| FR-6.2 | Governance Service | POST /api/v1/candidates/{reference_no}/deanonymize | Audit_Log | TS-GOV-002 | M-GOV-REASON-FIELD-COMPLETENESS | MVP-BLOCKER |
| FR-6.3 | Governance Service | POST /api/v1/candidates/{reference_no}/deanonymize | Audit_Log | TS-GOV-003 | M-GOV-AUDIT-EVENT-COVERAGE | MVP-BLOCKER |
| FR-6.4 | Governance Service | POST /api/v1/candidates/{reference_no}/deanonymize | Audit_Log | TS-GOV-004 | M-GOV-APPROVAL-POLICY-COMPLIANCE | MVP-BLOCKER |
| FR-7.1 | API Gateway | /api/v1/* | Audit_Log | TS-API-001 | M-API-VERSION-COVERAGE | MVP-BLOCKER |
| FR-7.2 | Matching Service | GET /api/v1/candidates/{reference_no}/score | Reference_Profile | TS-API-002 | M-API-SCORE-ENDPOINT-UPTIME | MVP-BLOCKER |
| FR-7.3 | Governance Service | POST /api/v1/candidates/{reference_no}/deanonymize | Mapping_Table, Audit_Log | TS-API-003 | M-API-DEANON-POLICY-ENFORCEMENT | MVP-BLOCKER |
| FR-7.4 | Recommendation Service | GET /api/v1/students/{user_id}/recommendations | Reference_Profile | TS-API-004 | M-API-RECOMMENDATION-UPTIME | MVP-BLOCKER |
| FR-7.5 | Django API Service | /api/v1/* | Audit_Log | TS-API-005 | M-API-ERROR-SCHEMA-COMPLIANCE | MVP-BLOCKER |
| FR-7.6 | Django API Service | /api/v1/* | Audit_Log | TS-API-006 | M-API-SESSION-AUTH-SUCCESS-RATE | MVP-BLOCKER |
| FR-7.7 | Django API Service | /api/v1/* | N/A | TS-API-007 | M-API-CORS-BLOCK-RATE | MVP-BLOCKER |
| FR-8.1 | Frontend SPA Service | N/A | N/A | TS-FE-001 | M-FE-BUILD-ARTIFACT-INTEGRITY | MVP-BLOCKER |
| FR-8.2 | Frontend SPA Service | /api/v1/* | N/A | TS-FE-002 | M-FE-API-ONLY-CALL-COMPLIANCE | MVP-BLOCKER |
| FR-8.3 | Frontend SPA Service | GET /api/v1/candidates/{reference_no}/score | Reference_Profile | TS-FE-003 | M-FE-ANON-LIST-DEFAULT-RATE | MVP-BLOCKER |
| FR-8.4 | Frontend SPA Service | POST /api/v1/candidates/{reference_no}/deanonymize | Audit_Log | TS-FE-004 | M-FE-DEANON-REASON-CAPTURE-RATE | MVP-BLOCKER |
| FR-8.5 | Frontend SPA Service | GET /api/v1/students/{user_id}/recommendations | Reference_Profile | TS-FE-005 | M-FE-STUDENT-DASHBOARD-SUCCESS | MVP-BLOCKER |
| FR-8.6 | Frontend SPA Service | N/A | N/A | TS-FE-006 | M-FE-RESPONSIVE-UI-PASS-RATE | MVP-BLOCKER |
| NFR-2.1 | Security Service | N/A | Primary_Profile, Reference_Profile | TS-SEC-001 | M-SEC-ATREST-ENCRYPTION-COVERAGE | MVP-BLOCKER |
| NFR-2.2 | Security Service | N/A | Audit_Log | TS-SEC-002 | M-SEC-KEY-ROTATION-AGE-DAYS | MVP-BLOCKER |
| NFR-2.3 | Security Service | /api/v1/* | N/A | TS-SEC-003 | M-SEC-TLS-ENFORCEMENT-RATE | MVP-BLOCKER |
| NFR-2.4 | Security Service | /api/v1/* | Audit_Log | TS-SEC-004 | M-SEC-LEAST-PRIVILEGE-VIOLATIONS | MVP-BLOCKER |
| NFR-2.5 | Django API Service | /api/v1/* | Audit_Log | TS-SEC-005 | M-SEC-DJANGO-MIDDLEWARE-COMPLIANCE | MVP-BLOCKER |
| NFR-2.6 | Frontend SPA Service | N/A | N/A | TS-SEC-006 | M-SEC-FRONTEND-SECRET-LEAK-INCIDENTS | MVP-BLOCKER |
| NFR-3.1 | Governance Service | GET /api/v1/candidates/{reference_no}/score | Reference_Profile | TS-COMP-001 | M-COMP-BLIND-MODE-DEFAULT-RATE | MVP-BLOCKER |
| NFR-3.2 | Explainability Service | GET /api/v1/candidates/{reference_no}/score | Reference_Profile | TS-COMP-002 | M-COMP-EXPLANATION-COVERAGE | MVP-BLOCKER |
| NFR-3.3 | Governance Service | N/A | Audit_Log | TS-COMP-003 | M-COMP-LOG-RETENTION-DAYS | MVP-BLOCKER |
| NFR-3.4 | Privacy Guard Service | N/A | Reference_Profile | TS-COMP-004 | M-COMP-REFSTORE-PII-INCIDENTS | MVP-BLOCKER |
| NFR-4.1 | Matching Service | POST /api/v1/candidates/{reference_no}/score | Reference_Profile | TS-SCALE-001 | M-SCALE-VECTOR-BACKEND-ABSTRACTION | MVP-BLOCKER |
| NFR-4.2 | Matching Service | POST /api/v1/candidates/{reference_no}/score | Reference_Profile | TS-SCALE-002 | M-SCALE-FILTER-QUERY-SUCCESS | MVP-BLOCKER |
| NFR-4.3 | Platform Service | N/A | Primary_Profile, Reference_Profile | TS-SCALE-003 | M-SCALE-PROFILE-CAPACITY | MVP-BLOCKER |
| NFR-5.1 | Observability Service | /api/v1/* | Audit_Log | TS-OBS-001 | M-OBS-TRACE-COVERAGE | MVP-BLOCKER |
| NFR-5.2 | Observability Service | /api/v1/* | Audit_Log | TS-OBS-002 | M-OBS-SLO-BREACH-RATE | MVP-BLOCKER |
| NFR-5.3 | Job Orchestrator Service | POST /api/v1/jobs/retry | Audit_Log | TS-OBS-003 | M-OBS-ASYNC-RETRY-SUCCESS | MVP-BLOCKER |
| NFR-5.4 | Django API Service | /api/v1/* | Audit_Log | TS-OBS-004 | M-OBS-CORRELATION-ID-COVERAGE | MVP-BLOCKER |
| NFR-5.5 | Frontend SPA Service | /api/v1/* | Audit_Log | TS-OBS-005 | M-OBS-FRONTEND-ERROR-CAPTURE-RATE | MVP-BLOCKER |

## 8. User Classes
1. Recruiters (HR): high-volume screening and shortlist operations.
2. Students/Job seekers: role discovery and upskilling.
3. University admins: cohort-level readiness tracking.
4. System admins: policy management, model governance, and audit operations.
