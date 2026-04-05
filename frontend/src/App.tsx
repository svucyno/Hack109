import { useMemo, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

type RoleView = "recruiter" | "student" | "admin";

type CandidateScore = {
  reference_no: string;
  score_normalized: number;
  score_bucket: number;
  explanation: string;
  matched_skills: string[];
  missing_skills: string[];
};

type StudentRecommendation = {
  role_path: string;
  confidence: number;
};

type CourseRecommendation = {
  title: string;
  provider: string;
  duration: string;
  level: string;
  url: string;
};

type StudentPayload = {
  recommendations: StudentRecommendation[];
  skill_gaps: string[];
  courses: CourseRecommendation[];
};

const MOCK_CANDIDATES: CandidateScore[] = [
  {
    reference_no: "REF-001",
    score_normalized: 0.91,
    score_bucket: 5,
    explanation: "Strong overlap in distributed systems, Python backend APIs, and event-driven architecture.",
    matched_skills: ["Python", "Django", "PostgreSQL", "REST"],
    missing_skills: ["Kubernetes"],
  },
  {
    reference_no: "REF-002",
    score_normalized: 0.78,
    score_bucket: 4,
    explanation: "Relevant API and data modeling experience with moderate gaps in observability tooling.",
    matched_skills: ["Python", "FastAPI", "Redis"],
    missing_skills: ["Prometheus", "OpenTelemetry"],
  },
  {
    reference_no: "REF-003",
    score_normalized: 0.63,
    score_bucket: 3,
    explanation: "Good fundamentals and project depth, but skill coverage is partial for senior profile requirements.",
    matched_skills: ["JavaScript", "Node.js", "SQL"],
    missing_skills: ["Django", "Vector Search"],
  },
];

const MOCK_STUDENT_PAYLOAD: StudentPayload = {
  recommendations: [
    { role_path: "Backend Engineer", confidence: 0.88 },
    { role_path: "ML Platform Associate", confidence: 0.73 },
    { role_path: "Data Engineer", confidence: 0.67 },
  ],
  skill_gaps: ["System Design", "Docker", "Model Evaluation Basics"],
  courses: [
    {
      title: "Scalable Backend Systems",
      provider: "Coursera",
      duration: "5 weeks",
      level: "Intermediate",
      url: "https://www.coursera.org",
    },
    {
      title: "Cloud Native Foundations",
      provider: "NPTEL",
      duration: "8 weeks",
      level: "Beginner",
      url: "https://nptel.ac.in",
    },
    {
      title: "ML Evaluation and Fairness",
      provider: "Coursera",
      duration: "4 weeks",
      level: "Intermediate",
      url: "https://www.coursera.org",
    },
  ],
};

async function pingBackend(): Promise<string> {
  const res = await fetch(`${API_BASE_URL}/auth/token/`, { method: "OPTIONS" });
  return res.ok ? "Backend reachable" : `Backend responded with ${res.status}`;
}

function toPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function App() {
  const [activeRole, setActiveRole] = useState<RoleView>("recruiter");
  const [backendStatus, setBackendStatus] = useState("Status: not checked");

  const [referenceNo, setReferenceNo] = useState("REF-001");
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateScore | null>(MOCK_CANDIDATES[0]);
  const [recruiterLoading, setRecruiterLoading] = useState(false);
  const [recruiterError, setRecruiterError] = useState("");

  const [reason, setReason] = useState("");
  const [confirmDeanon, setConfirmDeanon] = useState(false);
  const [deanonResult, setDeanonResult] = useState("");
  const [deanonLoading, setDeanonLoading] = useState(false);

  const [studentUserId, setStudentUserId] = useState("student-demo-001");
  const [studentPayload, setStudentPayload] = useState<StudentPayload | null>(null);
  const [studentLoading, setStudentLoading] = useState(false);
  const [studentError, setStudentError] = useState("");

  const deanonDisabled = !confirmDeanon || reason.trim().length < 10 || !selectedCandidate;

  const anonymousList = useMemo(() => {
    return [...MOCK_CANDIDATES].sort((a, b) => b.score_normalized - a.score_normalized);
  }, []);

  const runPing = async () => {
    setBackendStatus("Checking backend...");
    try {
      const result = await pingBackend();
      setBackendStatus(result);
    } catch {
      setBackendStatus("Backend unreachable. Check Django server and CORS settings.");
    }
  };

  const fetchCandidate = async () => {
    if (!referenceNo.trim()) {
      setRecruiterError("Enter a reference number to fetch a score.");
      return;
    }

    setRecruiterLoading(true);
    setRecruiterError("");
    try {
      const res = await fetch(`${API_BASE_URL}/candidates/${referenceNo.trim()}/score`);
      if (!res.ok) {
        throw new Error(`Endpoint unavailable (${res.status})`);
      }
      const data = (await res.json()) as CandidateScore;
      setSelectedCandidate(data);
    } catch {
      const fallback = MOCK_CANDIDATES.find((item) => item.reference_no === referenceNo.trim());
      if (fallback) {
        setSelectedCandidate(fallback);
      } else {
        setSelectedCandidate(null);
      }
      setRecruiterError("Using local Phase 1 mock data until matching endpoints are implemented.");
    } finally {
      setRecruiterLoading(false);
    }
  };

  const submitDeAnonymize = async () => {
    if (!selectedCandidate) return;

    setDeanonLoading(true);
    setDeanonResult("");
    try {
      const res = await fetch(`${API_BASE_URL}/candidates/${selectedCandidate.reference_no}/deanonymize`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ reason: reason.trim() }),
      });
      if (!res.ok) {
        throw new Error(`Policy endpoint unavailable (${res.status})`);
      }
      setDeanonResult("De-anonymization request submitted and logged for policy review.");
    } catch {
      setDeanonResult(
        "Governance endpoint is not live yet. UI validation passed and request payload is ready for Phase 4 integration."
      );
    } finally {
      setDeanonLoading(false);
    }
  };

  const loadStudentDashboard = async () => {
    if (!studentUserId.trim()) {
      setStudentError("Provide a user id to load recommendations.");
      return;
    }

    setStudentLoading(true);
    setStudentError("");
    try {
      const res = await fetch(`${API_BASE_URL}/students/${studentUserId.trim()}/recommendations`);
      if (!res.ok) {
        throw new Error(`Endpoint unavailable (${res.status})`);
      }
      const data = (await res.json()) as StudentPayload;
      setStudentPayload(data);
    } catch {
      setStudentPayload(MOCK_STUDENT_PAYLOAD);
      setStudentError("Using local Phase 1 student data until recommendation endpoints are implemented.");
    } finally {
      setStudentLoading(false);
    }
  };

  return (
    <div className="page">
      <header className="hero">
        <p className="eyebrow">GetHired Platform</p>
        <h1>Phase 1 Frontend Control Center</h1>
        <p className="subtitle">
          Split-data UX for recruiter, student, and governance flows with API-ready contracts under /api/v1.
        </p>
        <div className="actions">
          <button type="button" onClick={runPing}>
            Check Backend
          </button>
          <a href="http://127.0.0.1:8000/admin/" target="_blank" rel="noreferrer">
            Open Django Admin
          </a>
        </div>
        <p className="status">{backendStatus}</p>
      </header>

      <nav className="tabs" aria-label="Role switcher">
        <button type="button" className={activeRole === "recruiter" ? "tab active" : "tab"} onClick={() => setActiveRole("recruiter")}>
          Recruiter
        </button>
        <button type="button" className={activeRole === "student" ? "tab active" : "tab"} onClick={() => setActiveRole("student")}>
          Student
        </button>
        <button type="button" className={activeRole === "admin" ? "tab active" : "tab"} onClick={() => setActiveRole("admin")}>
          Admin
        </button>
      </nav>

      <main className="workspace">
        {activeRole === "recruiter" && (
          <section className="panel">
            <h2>Recruiter Blind Evaluation</h2>
            <p className="hint">Default list is anonymized and sorted by normalized score.</p>

            <div className="metrics-grid">
              {anonymousList.map((candidate) => (
                <article key={candidate.reference_no} className="metric-card">
                  <h3>{candidate.reference_no}</h3>
                  <p className="metric">{toPercent(candidate.score_normalized)}</p>
                  <p>Bucket {candidate.score_bucket}</p>
                </article>
              ))}
            </div>

            <div className="form-row">
              <label htmlFor="referenceNo">Reference no</label>
              <input
                id="referenceNo"
                value={referenceNo}
                onChange={(event) => setReferenceNo(event.target.value)}
                placeholder="REF-001"
              />
              <button type="button" onClick={fetchCandidate} disabled={recruiterLoading}>
                {recruiterLoading ? "Loading..." : "Fetch Score"}
              </button>
            </div>

            {recruiterError && <p className="alert">{recruiterError}</p>}

            {selectedCandidate && (
              <article className="details-card">
                <h3>Score Details: {selectedCandidate.reference_no}</h3>
                <p>{selectedCandidate.explanation}</p>
                <p>
                  Matched: <strong>{selectedCandidate.matched_skills.join(", ")}</strong>
                </p>
                <p>
                  Missing: <strong>{selectedCandidate.missing_skills.join(", ")}</strong>
                </p>
              </article>
            )}

            <article className="details-card">
              <h3>De-anonymization Request</h3>
              <p className="hint">Mandatory reason and explicit confirmation are required before submission.</p>
              <label htmlFor="reason">Reason (minimum 10 characters)</label>
              <textarea
                id="reason"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                placeholder="Example: final-round panel requires identity for interview scheduling."
              />
              <label className="checkline" htmlFor="confirmDeanon">
                <input
                  id="confirmDeanon"
                  type="checkbox"
                  checked={confirmDeanon}
                  onChange={(event) => setConfirmDeanon(event.target.checked)}
                />
                I confirm this action is policy compliant and will be audited.
              </label>
              <button type="button" disabled={deanonDisabled || deanonLoading} onClick={submitDeAnonymize}>
                {deanonLoading ? "Submitting..." : "Submit De-anonymize Request"}
              </button>
              {deanonResult && <p className="status-inline">{deanonResult}</p>}
            </article>
          </section>
        )}

        {activeRole === "student" && (
          <section className="panel">
            <h2>Student Career Dashboard</h2>
            <div className="form-row">
              <label htmlFor="studentUserId">User id</label>
              <input
                id="studentUserId"
                value={studentUserId}
                onChange={(event) => setStudentUserId(event.target.value)}
                placeholder="student-demo-001"
              />
              <button type="button" onClick={loadStudentDashboard} disabled={studentLoading}>
                {studentLoading ? "Loading..." : "Load Recommendations"}
              </button>
            </div>

            {studentError && <p className="alert">{studentError}</p>}

            {!studentPayload && !studentLoading && (
              <p className="hint">Load the dashboard to view role paths, skill gaps, and courses.</p>
            )}

            {studentPayload && (
              <div className="student-grid">
                <article className="details-card">
                  <h3>Recommended Role Paths</h3>
                  <ul>
                    {studentPayload.recommendations.map((item) => (
                      <li key={item.role_path}>
                        {item.role_path} - {toPercent(item.confidence)} confidence
                      </li>
                    ))}
                  </ul>
                </article>

                <article className="details-card">
                  <h3>Priority Skill Gaps</h3>
                  <ul>
                    {studentPayload.skill_gaps.map((gap) => (
                      <li key={gap}>{gap}</li>
                    ))}
                  </ul>
                </article>

                <article className="details-card">
                  <h3>Course Suggestions</h3>
                  <ul>
                    {studentPayload.courses.map((course) => (
                      <li key={course.title}>
                        <a href={course.url} target="_blank" rel="noreferrer">
                          {course.title}
                        </a>{" "}
                        ({course.provider}, {course.duration}, {course.level})
                      </li>
                    ))}
                  </ul>
                </article>
              </div>
            )}
          </section>
        )}

        {activeRole === "admin" && (
          <section className="panel">
            <h2>Governance Snapshot</h2>
            <p className="hint">Phase 1 placeholder for policy and fairness controls.</p>
            <div className="student-grid">
              <article className="details-card">
                <h3>Audit Coverage</h3>
                <p>Target: 100% de-anonymization and score override events logged.</p>
              </article>
              <article className="details-card">
                <h3>Fairness Gate</h3>
                <p>DIR policy threshold: pass when ratio is 0.80 or greater.</p>
              </article>
              <article className="details-card">
                <h3>API Contract</h3>
                <p>Frontend uses only {API_BASE_URL} endpoints and no direct datastore access.</p>
              </article>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
