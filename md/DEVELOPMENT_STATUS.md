# GetHired Development Status

Date: April 6, 2026
Source baseline: `md/prd.md` and `md/srs.md`

## 1. Executive Summary
Development has moved beyond the original backend-foundation stage. The project currently has a working end-to-end MVP flow for resume upload/parse, privacy validation, candidate scoring, student guidance, and admin visibility, with AI integration (Gemini/OpenRouter + fallback), caching, and allauth headless authentication.

Overall status by delivery maturity:
- Phase 1 (Foundation): Completed
- Phase 2 (Ingestion + Privacy): Mostly completed (OCR async fallback still pending)
- Phase 3 (Matching + Recommendations): Partially completed (rule/AI hybrid in place; true vector scoring pipeline pending)
- Phase 4 (Governance + Admin): Partially completed (admin visibility and access control done; approval workflow and immutable governance workflow pending)
- Phase 5 (NFR hardening and acceptance): In progress but not complete

## 2. What Has Been Delivered So Far

### 2.1 Platform and Core Architecture
- Django + DRF backend and React + Vite frontend are operational.
- Versioned API surface under `/api/v1` is active.
- Split-data model entities are implemented in schema (`PrimaryProfile`, `ReferenceProfile`, `MappingTable`, `AuditLog`).
- Resume upload pipeline supports local + pre-signed S3 upload flow.
- Environment profile workflow exists: `.env.dev`, `.env.prod`, `.env.example`.

### 2.2 Authentication and Security Posture
- JWT path has been removed from runtime flow.
- Auth now uses django-allauth headless session-token flow (`X-Session-Token`).
- CORS policy updated to allow session-token header for browser requests.
- Baseline security settings (HSTS/secure cookies/SSL toggles via env) are present.

### 2.3 Ingestion and Parsing
- Resume upload and registration endpoints are implemented.
- Resume parse endpoint exists and persists structured JSON to DB.
- File support includes PDF and DOCX.
- Legacy `.doc` upload is explicitly rejected with guidance.
- Skill, role, project, experience, education extraction logic exists with heuristic fallback.

### 2.4 Privacy Guard
- Privacy APIs are implemented (`redact`, `validate`, `report`).
- High-confidence PII blocking is implemented for validation flow.
- Redaction findings and summary reporting are returned by API.

### 2.5 Matching, AI, and Recommendations
- Candidate score endpoint is implemented (role-skill match based, with parsed profile support).
- Candidate de-anonymize request endpoint exists (reason validation + accepted response).
- Student recommendation endpoint exists with recommendation payload.
- AI layer includes:
  - Gemini integration
  - OpenRouter integration
  - smart fallback orchestration
  - role-focused resume analysis response mode
- AI result caching is implemented in JSONB (`parsed_json.ai_cache`) with request-signature + profile fingerprint invalidation.

### 2.6 Frontend Experience
- Role-specific routed pages exist: HR, Student, Admin.
- Student page supports upload, AI role paths, missing skills by role path, and growth roadmap.
- HR page supports suitability evaluation and analysis workflows.
- Admin page includes:
  - headless login
  - parsed records explorer
  - full parsed JSON / AI cache visibility

## 3. Phase Completion Against SRS/PRD

## Phase 1: Backend Foundation
Status: Done
Covered areas:
- Stack setup and dependency baseline
- Core settings and API scaffolding
- Canonical schema and service app structure
- Logging/error handling baseline

## Phase 2: Ingestion + Privacy Guard
Status: Mostly Done
Done:
- FR-1.1 upload acceptance
- FR-1.3 structured parsing output
- FR-2.1/2.2/2.4 privacy detection/redaction/validation behavior
- FR-2.3 report endpoint behavior
Partial/Pending:
- FR-1.2 OCR fallback is represented in flow but not fully implemented as robust async OCR pipeline
- Privacy currently relies on regex-style detection; Presidio/NER production-grade pipeline is pending

## Phase 3: Matching + Recommendation Engine
Status: Partial
Done:
- FR-4.2/4.3 score output and bucket behavior
- FR-4.4 explanation payload path
- FR-5.1/5.2/5.3 student recommendation shape and role-gap flow
- AI-assisted analysis/evaluation/recommendation endpoints operational
Partial/Pending:
- FR-4.1 strict embedding cosine-based scoring over de-identified vectors is not fully realized as production vector retrieval pipeline
- Embedding version enforcement and re-embedding operational workflow still pending

## Phase 4: Governance + De-anonymization
Status: Partial
Done:
- De-anonymize endpoint exists with reason-length validation
- Admin visibility page/API implemented for parsed data and AI cache inspection
- Admin auth now uses allauth headless session model
Partial/Pending:
- Full policy workflow for manager approval mode (FR-6.4) pending
- Immutable, comprehensive governance event lifecycle tied to all sensitive actions needs completion

## Phase 5: NFR Hardening, Observability, Acceptance Gate
Status: In Progress
Done:
- Structured logging framework exists
- Security configuration baseline exists
- Basic operational health checks are available
Pending:
- Full trace propagation and SLO dashboards
- Fairness automation/reporting pipeline
- Performance benchmarking against p95 SRS targets
- Complete acceptance test suites mapped to SRS traceability matrix

## 4. Requirement-Level Snapshot (High-Level)
- FR-1.x: Mostly complete
- FR-2.x: Mostly complete
- FR-3.x: Foundation complete
- FR-4.x: Partial
- FR-5.x: Partial to mostly complete
- FR-6.x: Partial
- FR-7.x: Mostly complete (headless auth migration completed)
- FR-8.x: Mostly complete for MVP role pages
- NFR-2.x: Baseline done, production hardening pending
- NFR-3.x: Partial
- NFR-4.x: Partial
- NFR-5.x: Partial

## 5. Current Project Position
The project is beyond foundation and in advanced MVP integration stage. Core user journeys are demonstrable, but several SRS-level production controls (vector rigor, governance depth, fairness/observability automation, OCR robustness) remain to reach full compliance.

## 6. Suggested Next Phase Focus
1. Complete production-grade ingestion/privacy pipeline:
   - async OCR implementation
   - Presidio/NER integration
   - stronger fail-closed validation
2. Complete vector-based matching stack:
   - embedding generation/indexing jobs
   - strict embedding-version checks
   - cosine retrieval consistency tests
3. Finish governance controls:
   - de-anonymization approval workflow
   - immutable audit coverage for all sensitive operations
4. Finalize NFR readiness:
   - latency/fairness test suites
   - trace coverage and dashboards
   - release gate checklist automation
