Product Requirements Document (PRD): AI Talent & Career Ecosystem
Date: April 4, 2026

Status: Defined (MVP Phase)

Target Domains: HR Recruitment & Student Career Development

1. Executive Summary
The Unified AI Talent Platform is an end-to-end "Skills-First" ecosystem designed to bridge the employability gap. For HR Professionals, it removes the "keyword wall" by ranking candidates based on semantic potential. For Students, it acts as a career co-pilot, identifying skill gaps and recommending trajectories. A core differentiator is the Split-Data Architecture, which ensures that AI evaluation is performed on de-identified data to eliminate bias and comply with the EU AI Act 2026.    

2. Problem Statement
Recruitment Inefficiency: HR teams face a "signal noise" crisis, with 70% of resumes being filtered out by rigid keyword-based ATS systems, often overlooking "hidden gems" who lack specific buzzwords.

The Guidance Gap: Students are often "prepared but not employable," lacking clear roadmaps to translate academic projects into industry-standard competencies.

Privacy & Bias: Traditional AI screening risks "demographic leakage," where personal identifiers (names, zip codes, schools) skew model outcomes.    

3. Target Personas
Persona	Role	Primary Goal	Key Pain Point
TA Manager	Recruiter	Surface the top 5% of talent in hours, not weeks.	Manual screening fatigue and inconsistent evaluation criteria.
Final-Year Student	Applicant	
Understand exactly what skills are needed for a target role. 

Generic career advice and black-box rejections.
University Admin	Advisor	Improve placement rates for their cohort.	
Scaling personalized guidance to thousands of students. 

  
4. Key Functional Features
4.1 Feature #6: Intelligent Split-Data Parser & Redactor
Logic: Upon upload, the system extracts text and uses Microsoft Presidio or NER models to identify PII.    

Primary Store: Encrypts and stores the full raw resume (PII included) linked to a internal User_ID.

Reference Store: Stores only de-identified skills, experiences, and project summaries linked to a unique Reference Number. Only this data is shared with the AI for scoring.

4.2 Feature #1: Explainable AI ATS Scoring (HR Domain)
Logic: Ranks the anonymized Reference_Profile against Job Descriptions (JD) using Cosine Similarity.

Formula:

Match Score= 
∥JD∥∥Resume∥
JD⋅Resume
​
 
Output: Provides an explainable 1–5 ranking. A "Reasoning Block" cites specific evidence (e.g., "Matched 85% due to 3+ years in Cloud Infrastructure") while hiding the candidate's name.    

4.3 Feature #5: Career Recommendation Engine (Student Domain)
Logic: Analyzes the Reference_Profile to suggest 3–5 potential career paths (e.g., "Based on your Math and Python projects, you match the FinTech Analyst path").

Visualization: Uses Plotly-generated donut charts to show path alignment.

4.4 Feature #7: Role Matcher & Skill Gap Analysis
Logic: Subtracts the user's skill vector from a target role vector to identify missing competencies.    

Action: Retrieves real-time course recommendations from Coursera or NPTEL APIs to bridge the gap.    

5. Technical Requirements & Database Strategy
5.1 Database Roadmap
MVP Phase: PostgreSQL + pgvector. Reintegration of AI results is handled via a simple SQL JOIN between the Primary_Store and Reference_Store using the Reference No. This ensures ACID compliance and data integrity for up to 5 million profiles.

Scaling Phase: Migrate the Reference_Store to Qdrant. This supports billion-scale vector search and "In-Graph Filtering," allowing HR to filter by anonymized criteria (e.g., "Must have PhD") during the vector search with sub-30ms latency.

5.2 Performance Benchmarks
Latency: First response for recommendations must be <0.5 seconds.

Accuracy: Achieve ≥87% correlation with expert human recruiters.

6. Success Metrics
Efficiency: Reduce HR "Time-to-Hire" by 30–50%.    

Equity: Maintain a Disparate Impact Ratio (DIR) of ≥0.80 to ensure fairness.

Readiness: 25% average improvement in student skill scores after using recommendations.    

7. Legal & Compliance (EU AI Act 2026)
As a "High-Risk" AI application (Recruitment), the system must:

Human Oversight (Art. 14): Provide a toggle for recruiters to "De-anonymize" and override AI rankings.    

Transparency (Art. 13): Include a "Right to Explanation" for any AI-driven rejection.

Audit Logging (Art. 12): Automatically log all data-split and evaluation events for 6+ months.

8. Out of Scope
Handling of live video interview feeds (Initial phase covers text-based screening only).

Automatic job applications (AI acts as a partner, not an author).

Post-hire payroll and benefits administration.    

