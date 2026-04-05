# Product Requirements Document (PRD): AI Talent and Career Ecosystem
Date: April 5, 2026
Status: Defined (MVP Build-Ready)
Version: 1.1

## 0. Implementation Stack Decision
Backend:
- Python 3.12+
- Django 5.x
- Django REST Framework for API layer

Frontend:
- React 18+
- Vite 5+ build tooling

Data and infra (MVP):
- PostgreSQL 16+ with pgvector
- Redis optional for async queue/cache

This PRD assumes a Django API-first architecture consumed by a React SPA.

## 1. Executive Summary
The AI Talent and Career Ecosystem is a skills-first platform for two domains:
- HR recruitment: semantic candidate ranking and explainable shortlisting.
- Student guidance: career path recommendations, skill gap detection, and course suggestions.

The core differentiator is a split-data architecture where AI services only process de-identified profile data linked by a Reference Number. Personally identifiable information (PII) remains isolated in a secured primary store.

## 2. Problem Statement
Recruitment inefficiency:
- Keyword-based filtering rejects qualified candidates lacking exact buzzwords.
- Recruiters spend excessive time on manual screening.

Guidance gap:
- Students lack concrete, role-specific, skill-building plans.
- Generic advice does not convert to employability outcomes.

Privacy and bias:
- Identity signals can leak into model decisions.
- High-risk AI usage in recruitment requires explainability, oversight, and auditability.

## 3. Personas and Jobs To Be Done
1. TA Manager (Recruiter)
- Goal: Identify top candidates in hours instead of weeks.
- Job to be done: Rank applicants by skill-match, review evidence, and de-anonymize only when justified.

2. Final-Year Student (Applicant)
- Goal: Understand target role fit and close missing skills.
- Job to be done: Receive role matches, skill gaps, and prioritized course actions.

3. University Admin (Advisor)
- Goal: Improve cohort placement outcomes at scale.
- Job to be done: Track student readiness trends and support intervention plans.

## 4. Product Scope (MVP)
In scope:
1. Resume upload and parsing (PDF/DOCX; OCR fallback for scanned PDFs).
2. PII detection and redaction pipeline.
3. Split-data persistence:
- Primary store: raw resume + PII metadata.
- Reference store: de-identified profile + embeddings.
4. Explainable ATS scoring against job descriptions.
5. Student role recommendation and skill-gap analysis.
6. External course recommendations (Coursera/NPTEL adapters).
7. Recruiter de-anonymization workflow with approvals and logging.
8. Dashboard visibility for recruiter, student, and admin roles.

Out of scope (MVP):
1. Video interview analysis.
2. Automatic job applications.
3. Post-hire payroll/benefits workflows.

## 5. Key Features and Product Decisions
### 5.1 Split-Data Parser and Redactor
- Extracts text and identifies PII using Presidio plus NER fallback.
- Stores original payload in primary store and de-identified payload in reference store.
- Blocks AI scoring if PII leakage checks fail.

### 5.2 Explainable ATS Scoring (HR)
- Uses cosine similarity between JD and resume embeddings.
- Formula:

$$
\text{cosine}(A, B) = \frac{A \cdot B}{\lVert A \rVert \lVert B \rVert}
$$

- Produces:
- normalized similarity score in [0,1]
- recruiter-facing rank bucket (1 to 5)
- reasoning block with evidence spans from de-identified text

### 5.3 Career Recommendation Engine (Student)
- Suggests 3 to 5 role paths from profile semantics and project history.
- Shows confidence per role and rationale highlights.
- Visualizes role alignment and skill category coverage.

### 5.4 Role Matcher and Skill Gap Analysis
- Computes missing competencies relative to target role profile.
- Prioritizes gaps by impact and dependency order.
- Recommends learning resources with metadata (duration, level, provider, language).

## 6. Product KPIs and Targets
Primary KPIs:
1. Time-to-hire reduction: 30% to 50% from baseline.
2. Recruiter quality correlation: at least 0.87 with expert recruiter scoring.
3. Student skill-readiness uplift: at least 25% average gain over baseline assessment.
4. Fairness KPI: Disparate Impact Ratio (DIR) at least 0.80 per monitored cohort.

Operational KPIs:
1. PII leakage rate into reference profiles: 0 critical leakages in production.
2. De-anonymization audit coverage: 100% of events logged.
3. Recommendation first-response latency: p95 less than 500 ms (for pre-embedded candidates).

## 7. Latency Budget (MVP)
To make the p95 target realistic, the pipeline is split into synchronous and asynchronous stages.

Synchronous serving path (recommendation request):
1. Candidate fetch + authorization: <= 50 ms
2. Vector similarity retrieval: <= 120 ms
3. Reasoning block generation (template-based extractive): <= 150 ms
4. Reintegration join and response assembly: <= 120 ms
Total p95 target: <= 440 ms

Asynchronous ingestion path (on upload):
1. Document extraction + OCR fallback: <= 1200 ms
2. PII detection and redaction: <= 1200 ms
3. Embedding generation + indexing: <= 1000 ms
Total target: <= 3400 ms

## 8. Compliance and Governance Requirements
1. Human oversight:
- Recruiters can request de-anonymization after threshold eligibility.
- Approval reason is mandatory and immutable in logs.

2. Transparency:
- Each ranking decision exposes a user-readable explanation including key matched skills and missing requirements.

3. Audit logging:
- Log all split, score, de-anonymize, and override actions.
- Retention minimum: 6 months (configurable to 12 months).

4. Data minimization:
- AI services receive only de-identified payloads.
- No direct access from model service to primary store.

## 9. Fairness Evaluation Policy (MVP)
1. Evaluation cadence:
- Weekly automated fairness report.
- Monthly governance review.

2. Metrics:
- DIR as primary gate.
- Secondary checks: score parity and false-negative parity by cohort.

3. Action thresholds:
- DIR >= 0.80: pass.
- 0.70 <= DIR < 0.80: warning, mandatory review ticket.
- DIR < 0.70: fail, release gate for model changes.

4. Controls:
- Versioned model and embedding rollouts with rollback switch.
- Pre-production fairness regression required before promotion.

## 10. Release Plan
MVP release criteria:
1. All in-scope features implemented.
2. Security and compliance checks passed.
3. Acceptance tests passed for:
- PII leakage
- ATS ranking consistency
- latency p95
- de-anonymization logging
- fairness thresholds

Post-MVP roadmap:
1. Qdrant migration when profile volume and latency justify scale-out.
2. Multi-language resume parsing and domain-specific ontologies.
3. Advanced advisor analytics for university cohorts.
