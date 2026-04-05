import { useEffect, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

type RolePage = "hr" | "student" | "admin";

type HrOverview = {
  role: string;
  title: string;
  description: string;
  candidate_refs: string[];
};

type StudentOverview = {
  role: string;
  title: string;
  description: string;
  default_user: string;
};

type AdminOverview = {
  role: string;
  title: string;
  description: string;
  metrics: {
    deanonymize_audit_target: string;
    fairness_dir_threshold: string;
  };
};

type CandidateScore = {
  reference_no: string;
  score_normalized: number;
  score_bucket: number;
  explanation: string;
  matched_skills: string[];
  missing_skills: string[];
};

type StudentPayload = {
  recommendations: Array<{ role_path: string; confidence: number }>;
  skill_gaps: string[];
  courses: Array<{ title: string; provider: string; duration: string; level: string; url: string }>;
};

type ParsePayload = {
  reference_no: string;
  structured_profile: {
    skills: string[];
    years_experience: number | null;
  };
  parse_meta: {
    storage_backend: string;
    storage_key: string;
  };
};

function toPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function App() {
  const [page, setPage] = useState<RolePage>("hr");

  const [hrOverview, setHrOverview] = useState<HrOverview | null>(null);
  const [studentOverview, setStudentOverview] = useState<StudentOverview | null>(null);
  const [adminOverview, setAdminOverview] = useState<AdminOverview | null>(null);
  const [overviewError, setOverviewError] = useState("");

  const [referenceNo, setReferenceNo] = useState("REF-001");
  const [candidateScore, setCandidateScore] = useState<CandidateScore | null>(null);
  const [scoreError, setScoreError] = useState("");

  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [uploadError, setUploadError] = useState("");
  const [lastReferenceNo, setLastReferenceNo] = useState("");
  const [parsePayload, setParsePayload] = useState<ParsePayload | null>(null);

  const [studentUserId, setStudentUserId] = useState("student-demo-001");
  const [studentPayload, setStudentPayload] = useState<StudentPayload | null>(null);
  const [studentError, setStudentError] = useState("");

  const [adminValidationText, setAdminValidationText] = useState("This profile has no private contact details.");
  const [adminValidationResult, setAdminValidationResult] = useState("");

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadOverviews = async () => {
      setOverviewError("");
      try {
        const [hrRes, studentRes, adminRes] = await Promise.all([
          fetch(`${API_BASE_URL}/hr`),
          fetch(`${API_BASE_URL}/student`),
          fetch(`${API_BASE_URL}/admin`),
        ]);
        if (!hrRes.ok || !studentRes.ok || !adminRes.ok) {
          throw new Error("overview endpoints unavailable");
        }

        const hrData = (await hrRes.json()) as HrOverview;
        const studentData = (await studentRes.json()) as StudentOverview;
        const adminData = (await adminRes.json()) as AdminOverview;

        setHrOverview(hrData);
        setStudentOverview(studentData);
        setAdminOverview(adminData);
        setStudentUserId(studentData.default_user || "student-demo-001");
      } catch {
        setOverviewError("Failed to load role pages from backend endpoints.");
      }
    };

    void loadOverviews();
  }, []);

  const fetchScore = async () => {
    setLoading(true);
    setScoreError("");
    try {
      const res = await fetch(`${API_BASE_URL}/candidates/${referenceNo.trim()}/score`);
      if (!res.ok) {
        throw new Error("score endpoint failed");
      }
      setCandidateScore((await res.json()) as CandidateScore);
    } catch {
      setScoreError("Score endpoint failed for this reference.");
      setCandidateScore(null);
    } finally {
      setLoading(false);
    }
  };

  const uploadResume = async () => {
    if (!resumeFile) {
      setUploadError("Select a PDF file first.");
      return;
    }

    setLoading(true);
    setUploadError("");
    setUploadStatus("");

    try {
      const presignedRes = await fetch(`${API_BASE_URL}/resumes/upload-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: resumeFile.name, content_type: resumeFile.type || "application/pdf" }),
      });

      if (presignedRes.ok) {
        const pre = (await presignedRes.json()) as {
          reference_no: string;
          upload_url: string;
          s3_key: string;
        };

        const putRes = await fetch(pre.upload_url, {
          method: "PUT",
          body: resumeFile,
        });

        if (!putRes.ok) {
          throw new Error(`S3 upload failed (${putRes.status})`);
        }

        const registerRes = await fetch(`${API_BASE_URL}/resumes/register-upload`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            reference_no: pre.reference_no,
            s3_key: pre.s3_key,
            filename: resumeFile.name,
            content_type: resumeFile.type || "application/pdf",
          }),
        });

        if (!registerRes.ok) {
          const registerError = await registerRes.text();
          throw new Error(`register failed (${registerRes.status}) ${registerError}`);
        }

        setLastReferenceNo(pre.reference_no);
        setUploadStatus(`Uploaded to S3 with key: ${pre.s3_key}`);
        return;
      }

      const preError = await presignedRes.text();
      throw new Error(`upload-url failed (${presignedRes.status}) ${preError}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Upload failed.";
      setUploadError(message);
    } finally {
      setLoading(false);
    }
  };

  const parseResume = async () => {
    if (!lastReferenceNo.trim()) {
      setUploadError("Upload a resume first to get a reference number.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/resumes/${lastReferenceNo}/parse`, { method: "POST" });
      if (!res.ok) {
        throw new Error("parse failed");
      }
      setParsePayload((await res.json()) as ParsePayload);
    } catch {
      setUploadError("Parse failed for the uploaded reference.");
    } finally {
      setLoading(false);
    }
  };

  const loadStudent = async () => {
    setLoading(true);
    setStudentError("");
    try {
      const res = await fetch(`${API_BASE_URL}/students/${studentUserId.trim()}/recommendations`);
      if (!res.ok) {
        throw new Error("student endpoint failed");
      }
      setStudentPayload((await res.json()) as StudentPayload);
    } catch {
      setStudentError("Failed to load student recommendations from backend.");
      setStudentPayload(null);
    } finally {
      setLoading(false);
    }
  };

  const runAdminValidation = async () => {
    setLoading(true);
    setAdminValidationResult("");
    try {
      const res = await fetch(`${API_BASE_URL}/privacy/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: adminValidationText }),
      });

      if (res.ok) {
        const data = (await res.json()) as { status: string; message: string };
        setAdminValidationResult(`${data.status.toUpperCase()}: ${data.message}`);
      } else {
        setAdminValidationResult("BLOCKED: high-confidence PII detected.");
      }
    } catch {
      setAdminValidationResult("Validation endpoint unavailable.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="shell">
      <header className="masthead">
        <p className="tag">GetHired v2</p>
        <h1>Role-Specific Portal</h1>
        <p>Three dedicated pages powered by individual backend endpoints for HR, Student, and Admin.</p>
      </header>

      <nav className="role-nav" aria-label="role navigation">
        <button className={page === "hr" ? "active" : ""} onClick={() => setPage("hr")} type="button">
          HR Page
        </button>
        <button className={page === "student" ? "active" : ""} onClick={() => setPage("student")} type="button">
          Student Page
        </button>
        <button className={page === "admin" ? "active" : ""} onClick={() => setPage("admin")} type="button">
          Admin Page
        </button>
      </nav>

      {overviewError && <p className="error">{overviewError}</p>}

      {page === "hr" && (
        <section className="panel">
          <h2>{hrOverview?.title || "HR Talent Dashboard"}</h2>
          <p>{hrOverview?.description}</p>

          <div className="card-grid">
            <article className="card">
              <h3>Candidate Scoring</h3>
              <input value={referenceNo} onChange={(e) => setReferenceNo(e.target.value)} placeholder="REF-001" />
              <button onClick={fetchScore} type="button" disabled={loading}>
                Fetch Score
              </button>
              {scoreError && <p className="error">{scoreError}</p>}
              {candidateScore && (
                <div className="result">
                  <p>
                    <strong>{candidateScore.reference_no}</strong> - {toPercent(candidateScore.score_normalized)} (bucket {candidateScore.score_bucket})
                  </p>
                  <p>{candidateScore.explanation}</p>
                </div>
              )}
            </article>

            <article className="card">
              <h3>Resume Upload</h3>
              <input type="file" accept=".pdf" onChange={(e) => setResumeFile(e.target.files?.[0] || null)} />
              <button onClick={uploadResume} type="button" disabled={loading}>
                Upload Resume
              </button>
              <button onClick={parseResume} type="button" disabled={loading || !lastReferenceNo}>
                Parse Uploaded Resume
              </button>
              {uploadStatus && <p className="ok">{uploadStatus}</p>}
              {uploadError && <p className="error">{uploadError}</p>}
              {lastReferenceNo && <p className="meta">Reference: {lastReferenceNo}</p>}
              {parsePayload && (
                <div className="result">
                  <p>
                    Skills: <strong>{parsePayload.structured_profile.skills.join(", ") || "None"}</strong>
                  </p>
                  <p>
                    Storage: {parsePayload.parse_meta.storage_backend} ({parsePayload.parse_meta.storage_key})
                  </p>
                </div>
              )}
            </article>
          </div>
        </section>
      )}

      {page === "student" && (
        <section className="panel">
          <h2>{studentOverview?.title || "Student Career Page"}</h2>
          <p>{studentOverview?.description}</p>
          <div className="card">
            <label htmlFor="studentId">Student id</label>
            <input id="studentId" value={studentUserId} onChange={(e) => setStudentUserId(e.target.value)} />
            <button type="button" onClick={loadStudent} disabled={loading}>
              Load Recommendations
            </button>
            {studentError && <p className="error">{studentError}</p>}
            {studentPayload && (
              <div className="result">
                <h3>Role Paths</h3>
                <ul>
                  {studentPayload.recommendations.map((r) => (
                    <li key={r.role_path}>
                      {r.role_path} - {toPercent(r.confidence)}
                    </li>
                  ))}
                </ul>
                <h3>Skill Gaps</h3>
                <ul>
                  {studentPayload.skill_gaps.map((g) => (
                    <li key={g}>{g}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </section>
      )}

      {page === "admin" && (
        <section className="panel">
          <h2>{adminOverview?.title || "Admin Governance Page"}</h2>
          <p>{adminOverview?.description}</p>
          <div className="card-grid">
            <article className="card">
              <h3>Governance Metrics</h3>
              <p>Audit target: {adminOverview?.metrics.deanonymize_audit_target}</p>
              <p>DIR threshold: {adminOverview?.metrics.fairness_dir_threshold}</p>
            </article>
            <article className="card">
              <h3>PII Validation</h3>
              <textarea value={adminValidationText} onChange={(e) => setAdminValidationText(e.target.value)} />
              <button type="button" onClick={runAdminValidation} disabled={loading}>
                Validate Privacy
              </button>
              {adminValidationResult && <p className="meta">{adminValidationResult}</p>}
            </article>
          </div>
        </section>
      )}
    </div>
  );
}

export default App;
