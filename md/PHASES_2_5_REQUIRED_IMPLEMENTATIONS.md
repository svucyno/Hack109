# Required Implementations for Phase 2, 3, 4, and 5

Date: April 6, 2026
Source reference: `md/prd.md`, `md/srs.md`, `md/DEVELOPMENT_STATUS.md`

This document lists the remaining implementation work needed to complete Phases 2-5.

## Phase 2: Ingestion + Privacy Guard (Remaining)

### Scope covered by SRS
- FR-1.2
- FR-2.1
- FR-2.2
- FR-2.3
- FR-2.4

### Required implementation list
1. Implement production OCR fallback pipeline for scanned PDFs (FR-1.2).
2. Add text extraction confidence scoring and threshold-based OCR trigger (FR-1.2).
3. Move OCR and heavy parsing steps to async worker tasks with retries and idempotency keys (NFR-5.3).
4. Integrate Presidio and/or transformer NER fallback for robust PII detection beyond regex rules (FR-2.1).
5. Enforce fail-closed pipeline behavior so unresolved high-confidence PII blocks downstream scoring (FR-2.4).
6. Persist redaction reports in durable storage with reference linkage and confidence summary (FR-2.3).
7. Add structured PII entity policy configuration (entity allow/block lists and thresholds) per environment.
8. Add regression tests for PDF text, DOCX text, scanned PDF OCR fallback, and malformed-file handling.
9. Add privacy test suite for true/false positives and leakage prevention coverage.
10. Add ingestion observability metrics for extraction success rate, OCR fallback rate, parse coverage, and failure reasons.

### Done criteria for Phase 2 completion
1. OCR fallback executes automatically for scanned PDFs in async pipeline.
2. Presidio/NER-backed privacy detection is active and tested.
3. No downstream scoring for records failing leakage validation.
4. Durable redaction reports available by reference id.
5. CI tests cover ingestion and privacy failure/edge cases.

## Phase 3: Matching + Recommendation Engine (Remaining)

### Scope covered by SRS
- FR-4.1
- FR-4.2
- FR-4.3
- FR-4.4
- FR-4.5
- FR-5.1
- FR-5.2
- FR-5.3
- SRS 3.3 embedding contract

### Required implementation list
1. Implement true embedding generation and persistent indexing for de-identified profiles (FR-4.1).
2. Add vector retrieval/scoring using cosine similarity over stored vectors only (FR-4.1).
3. Enforce embedding_version compatibility checks during scoring (SRS 3.3).
4. Implement re-embedding workflow for model_version or embedding_version changes (SRS 3.3).
5. Replace placeholder/rule-only matching paths with vector-first scoring while preserving safe fallback.
6. Harden score normalization and bucket threshold configuration with test validation (FR-4.2/FR-4.3).
7. Standardize explanation payload with evidence snippets and missing skills schema (FR-4.4).
8. Add identity leakage guard on explanation outputs to recruiter-facing endpoints (FR-4.5).
9. Improve student recommendations from static/template outputs to profile- and role-grounded generation (FR-5.1/FR-5.2).
10. Integrate provider-backed course adapters with real metadata validation (URL, duration, level) (FR-5.3).
11. Add ranking-quality benchmark tests and calibration against recruiter labels.
12. Add performance tests for vector retrieval and recommendation latency budget compliance.

### Done criteria for Phase 3 completion
1. Candidate scoring uses stored de-identified vectors in production path.
2. Version mismatch checks prevent invalid vector comparisons.
3. Recommendation outputs are profile-grounded and non-template.
4. Explanation schema is consistent and identity-safe.
5. Quality and latency tests meet defined thresholds.

## Phase 4: Governance + De-anonymization (Remaining)

### Scope covered by SRS
- FR-6.1
- FR-6.2
- FR-6.3
- FR-6.4
- NFR-3.1
- NFR-3.3

### Required implementation list
1. Enforce strict RBAC on de-anonymization endpoint and related admin operations (FR-6.1).
2. Enforce mandatory reason capture with schema validation and minimum quality checks (FR-6.2).
3. Persist de-anonymization and override events in immutable audit trail records (FR-6.3).
4. Implement manager-approval policy mode with request, approve, deny states (FR-6.4).
5. Add governance APIs/UI for approval queue and decision history.
6. Add override workflow with explicit rationale, actor trace, and before/after score snapshots.
7. Add tamper-resistant audit guarantees (append-only behavior and restricted update/delete paths).
8. Enforce blind-evaluation defaults in recruiter list and score responses (NFR-3.1).
9. Add governance tests for unauthorized access, missing reason, policy state transitions, and audit completeness.
10. Add retention job/policy to satisfy audit log retention requirement (NFR-3.3).

### Done criteria for Phase 4 completion
1. All sensitive governance actions are role-protected and reason-bound.
2. Approval mode works end to end with full audit visibility.
3. Audit trail is immutable in practice and verified by tests.
4. Blind mode is default for recruiter flows.

## Phase 5: NFR Hardening + Acceptance Gate (Remaining)

### Scope covered by SRS
- NFR-2.x
- NFR-3.x
- NFR-4.x
- NFR-5.x
- Section 6 fairness governance
- Section 7 verification and acceptance

### Required implementation list
1. Implement end-to-end trace id propagation across API, workers, and async jobs (NFR-5.1).
2. Add SLO/error-budget dashboards for API latency, failures, and async pipeline health (NFR-5.2).
3. Add robust retry/backoff/idempotency handling for failed background jobs (NFR-5.3).
4. Enforce structured logging coverage for all critical endpoints and worker tasks (NFR-5.4).
5. Implement frontend error telemetry pipeline for failed API/render interactions (NFR-5.5).
6. Implement KMS-backed key management and rotation workflow for encryption key versions (NFR-2.2).
7. Add security hardening checks for TLS-only transport and least-privilege service identities (NFR-2.3/NFR-2.4).
8. Add automated PII leakage gate tests in CI/CD (NFR-3.4).
9. Implement fairness reporting pipeline (weekly automation + monthly review artifacts).
10. Add DIR threshold enforcement as release gate for model changes.
11. Execute scale and load tests for profile volume and query behavior (NFR-4.2/NFR-4.3).
12. Build complete requirement-to-test-to-metric traceability closure from SRS matrix.

### Done criteria for Phase 5 completion
1. NFR dashboards and alerts are operational.
2. Fairness and leakage gates block unsafe releases.
3. Performance and reliability targets are test-verified.
4. Requirement traceability matrix has automated evidence for all MVP-blocker rows.

## Recommended Execution Order (Practical)
1. Finish Phase 2 first (OCR + Presidio/NER + fail-closed).
2. Complete vector-first scoring core in Phase 3.
3. Implement approval workflow and immutable audit guarantees in Phase 4.
4. Close observability/fairness/performance gates in Phase 5.

## Suggested Milestone Exit Checklist
1. Code implemented and merged for all items marked required.
2. API contracts documented and validated.
3. Automated tests passing for FR/NFR scope of the phase.
4. Metrics/dashboard evidence attached for release review.
5. Phase sign-off note added to `md/` with date and owner.
