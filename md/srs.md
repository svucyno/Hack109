This Software Requirements Specification (SRS) details the development of an AI talent platform using a **Split-Data Architecture**. This model ensures that personally identifiable information (PII) is isolated from the AI evaluation process to prevent bias and enhance security, while maintaining a clear path for data reintegration and future scaling.

---

# Software Requirements Specification (SRS): AI Talent & Career Ecosystem

## 1. Introduction
### 1.1 Purpose
The purpose of this document is to define the technical requirements for a dual-domain AI platform that serves HR professionals and students. The system architecture specifically addresses privacy by separating sensitive user data from de-identified evaluation data via a unique **Reference Number**.

### 1.2 System Scope
The system consists of a **Privacy Guard** (PII removal), a **Dual-Database Layer** (Primary/Reference), an **Evaluation Engine** (Semantic Matching), and a **Reintegration Agent** (Result Mapping).

---

## 2. Architecture Overview: The Split-Data Model
The system follows a privacy-by-design approach where the AI "sees" only competencies, not identities.

1.  **Ingestion:** The user uploads a resume (PDF/DOCX).
2.  **Privacy Pass:** The system identifies and extracts PII (Name, Email, Phone, Address, Links).
3.  **Data Split:**
    *   **Primary Store:** Encrypts and stores the full resume and PII linked to a `User_ID`.
    *   **Reference Store:** Stores anonymized skills, project summaries, and vector embeddings linked only to a `Reference_No`.
4.  **AI Evaluation:** The AI Matcher processes the `Reference_No` profile against Job Descriptions.
5.  **Reintegration:** The result is saved to the Reference entry. The system then "joins" this result back to the Primary entry using the `Reference_No` to notify the user.

---

## 3. Database Strategy: MVP to Scale Upgrade

### 3.1 MVP Choice: PostgreSQL + pgvector
For the MVP, **PostgreSQL with the pgvector extension** is the recommended foundation.
*   **Rationale:** It handles both relational data (the mapping of `Reference_No` to `User_ID`) and vector similarity in one ACID-compliant engine. Reintegration is a simple SQL `JOIN`.
*   **Limit:** Highly effective for up to 5 million profiles.

### 3.2 Future Upgrade: Qdrant
When the platform scales beyond 5-10 million resumes, the system shall migrate the Reference Store to **Qdrant**.
*   **Rationale:** Qdrant is built in Rust for high-performance vector operations and supports "Filterable HNSW". This allows HR to filter by anonymized criteria (e.g., "minimum 3 years experience") *during* the vector search, providing sub-30ms latency at massive scale.

---

## 4. Functional Requirements

### 4.1 PII De-identification Module (Privacy Guard)
*   **FR-1.1 (Detection):** The system shall utilize **Microsoft Presidio** or the `en_core_web_trf` transformer model to identify PII entities in unstructured text.
*   **FR-1.2 (Redaction):** The system shall redact or mask the following entities: `PERSON`, `EMAIL_ADDRESS`, `PHONE_NUMBER`, `LOCATION`, and `URL`.
*   **FR-1.3 (Prestige Bias Mitigation):** The system shall optionally replace specific university names with generic educational tiers (e.g., "Tier 1 University") to ensure purely skill-based evaluation.

### 4.2 Data Splitting and Storage logic
*   **FR-2.1 (Primary Storage):** The system shall store the original resume file and PII in a `Primary_Profile` table, encrypted using AES-256.[1, 2]
*   **FR-2.2 (Reference Storage):** The system shall store an anonymized JSON object of skills and experiences in a `Reference_Profile` table, identified only by an auto-generated `Reference_No`.
*   **FR-2.3 (Embedding Generation):** The system shall generate dense vector representations of the `Reference_Profile` using `text-embedding-3-small` or `all-MiniLM-L6-v2`.[3, 4]

### 4.3 Evaluation and Reintegration
*   **FR-3.1 (Blind Evaluation):** The AI scoring engine shall only have access to the Reference Store. No PII shall be sent to the AI during the matching process.
*   **FR-3.2 (Result Declaration):** When a match score or career path is generated, the system shall update the `Reference_Profile` with a `result_status` and `score`.
*   **FR-3.3 (Mapping/Joins):** The Reintegration Agent shall perform a lookup: 
    *   `GET User_ID FROM Mapping_Table WHERE Reference_No = Current_Result.Reference_No`
*   **FR-3.4 (User Visibility):** The final result shall be pushed to the user’s dashboard, merging the AI insights with their primary identity data for display.

---

## 5. Non-Functional Requirements

### 5.1 Privacy and Compliance
*   **Blind Hiring Mode:** HR users shall not see PII in the candidate list until the candidate surpasses a defined "Match Score" threshold (e.g., 0.75).
*   **Auditability:** The system shall maintain a log of every "De-anonymization" event to comply with Art. 12 of the EU AI Act.

### 5.2 Performance and Latency
*   **Parsing Speed:** PII extraction and data splitting shall complete in $<3$ seconds per resume.
*   **Retrieval Latency:** Result reintegration (the join between Primary and Reference data) shall occur in $<200$ms to ensure real-time dashboard updates.[5]

### 5.3 Scalability Path
*   The architecture shall use **RESTful API endpoints** for the AI Matcher so that `pgvector` can be swapped for a distributed `Qdrant` cluster in the future without changing the Primary Store logic.

---

## 6. Verification and Traceability
Each requirement will be verified through **Automated Bias Audits** (calculating the Disparate Impact Ratio) and **PII Leakage Tests** (checking if any names or numbers persist in the Reference Store).




## the system includes:

Module A (The Privacy Guard): Automated PII de-identification and anonymization.

Module B (The Parser): Semantic data extraction from unstructured resumes.

Module C (HR Suite): Unbiased ATS scoring, ranking, and candidate evaluation.

Module D (Student Suite): Career roadmapping, skill gap analysis, and course recommendations.

## Definitions and Acronyms
PII: Personally Identifiable Information (Names, Phone, Address, etc.).

NER: Named Entity Recognition (ML technique to identify entities in text).

ATS: Applicant Tracking System.

Cosine Similarity: Metric used to measure the distance between two vectors.

## User Classes and Characteristics
Recruiters (HR): High-volume users focused on efficiency and bias reduction.

Students/Job Seekers: Users requiring guidance, upskilling, and career matching.

System Admins: Responsible for monitoring bias audits and model performance.