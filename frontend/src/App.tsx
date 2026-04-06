import { useEffect, useMemo, useState } from "react";
import { BrowserRouter, NavLink, Navigate, Route, Routes } from "react-router-dom";

const RAW_API_URL =
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_BACKEND_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

const API_BASE_URL = RAW_API_URL.endsWith("/api/v1")
  ? RAW_API_URL
  : `${RAW_API_URL.replace(/\/+$/, "")}/api/v1`;

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

type AdminRecordSummary = {
  reference_no: string;
  status: string;
  original_filename: string;
  content_type: string;
  storage_backend: string;
  storage_key: string;
  object_size: number | null;
  object_etag: string;
  parsed_at: string | null;
  created_at: string;
  updated_at: string;
  skills: string[];
  roles: string[];
  years_experience: number | null;
  ai_cache_keys: string[];
};

type AdminRecordListResponse = {
  count: number;
  results: AdminRecordSummary[];
};

type AdminRecordDetailResponse = {
  reference_no: string;
  status: string;
  original_filename: string;
  content_type: string;
  storage_backend: string;
  storage_key: string;
  object_size: number | null;
  object_etag: string;
  parsed_at: string | null;
  created_at: string;
  updated_at: string;
  parsed_json: Record<string, unknown>;
};

type VerifiedLink = {
  url: string;
  domain?: string;
  type?: string;
  reachable?: boolean;
  status_code?: number | null;
  verified_at?: string;
  error?: string;
};

type CandidateScore = {
  reference_no: string;
  score_normalized: number;
  score_bucket: number;
  explanation: string;
  matched_skills: string[];
  missing_skills: string[];
};

type HrAiAnalysis = {
  status: string;
  reference_no: string;
  ai_analysis: {
    job_roles?: string[];
  };
  provider?: string;
  model?: string;
  cache_hit?: boolean;
};

type HrSuitabilityResponse = {
  status: string;
  reference_no: string;
  comparison?: {
    fit_score: number;
    fit_threshold_passed: boolean;
    experience_threshold_passed: boolean;
    decision: "PASS" | "NOT_PASS";
    is_resume_suitable: boolean;
  };
  ai_evaluation?: {
    strengths?: string[];
    gaps?: string[];
    recommendations?: string[];
    reasoning?: string;
  };
  evaluation_input?: {
    role_name?: string;
    required_skills?: string[];
    min_fit_score?: number;
    required_experience_years?: number | null;
  };
  provider?: string;
  model?: string;
  cache_hit?: boolean;
};

type ParsePayload = {
  reference_no: string;
  structured_profile: {
    skills: string[];
    roles: string[];
    years_experience: number | null;
    links?: string[];
    verified_links?: VerifiedLink[];
    job_relevant_skills?: {
      matched: string[];
      missing: string[];
      role_requirements: Record<string, string[]>;
    };
  };
  parse_meta: {
    storage_backend: string;
    storage_key: string;
  };
};

type AiRoleAnalysisPayload = {
  status: string;
  reference_no: string;
  ai_analysis: {
    job_roles: string[];
  };
  provider?: string;
  model?: string;
  cache_hit?: boolean;
};

type RoleSkillView = {
  role: string;
  matched_skills: string[];
  missing_skills: string[];
  score_normalized: number;
};

type CareerRecommendationPayload = {
  recommendations?: {
    skill_roadmap?: Record<string, string[]>;
    timeline?: string;
  };
  cache_hit?: boolean;
};

const DEFAULT_ADMIN_OVERVIEW: AdminOverview = {
  role: "admin",
  title: "Admin Governance Page",
  description: "Audit coverage, fairness checks, and policy controls.",
  metrics: {
    deanonymize_audit_target: "100%",
    fairness_dir_threshold: "0.80",
  },
};

function toPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function normalizeLinks(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .filter((item): item is string => typeof item === "string")
    .map((item) => item.trim())
    .filter(Boolean);
}

function normalizeVerifiedLinks(value: unknown): VerifiedLink[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .filter((item): item is VerifiedLink => Boolean(item) && typeof item === "object" && "url" in item)
    .map((item) => ({
      url: String(item.url || "").trim(),
      domain: typeof item.domain === "string" ? item.domain : undefined,
      type: typeof item.type === "string" ? item.type : undefined,
      reachable: typeof item.reachable === "boolean" ? item.reachable : undefined,
      status_code: typeof item.status_code === "number" ? item.status_code : null,
      verified_at: typeof item.verified_at === "string" ? item.verified_at : undefined,
      error: typeof item.error === "string" ? item.error : undefined,
    }))
    .filter((item) => Boolean(item.url));
}

function extractLinksFromParsedJson(parsedJson: unknown): { links: string[]; verifiedLinks: VerifiedLink[] } {
  if (!parsedJson || typeof parsedJson !== "object") {
    return { links: [], verifiedLinks: [] };
  }

  const structuredProfile = (parsedJson as { structured_profile?: Record<string, unknown> }).structured_profile;
  if (!structuredProfile || typeof structuredProfile !== "object") {
    return { links: [], verifiedLinks: [] };
  }

  return {
    links: normalizeLinks(structuredProfile.links),
    verifiedLinks: normalizeVerifiedLinks(structuredProfile.verified_links),
  };
}

function LinkList(props: { links: string[]; verifiedLinks?: VerifiedLink[] }) {
  const { links, verifiedLinks = [] } = props;
  const verifiedMap = new Map(verifiedLinks.map((item) => [item.url, item] as const));

  if (!links.length) {
    return <p className="meta">No resume links were extracted.</p>;
  }

  return (
    <div className="link-list">
      {links.map((link) => {
        const verified = verifiedMap.get(link);
        const reachable = verified?.reachable;
        const linkType = verified?.type || "link";

        return (
          <a
            key={link}
            className={`link-pill${reachable === false ? " is-unreachable" : ""}`}
            href={link}
            target="_blank"
            rel="noreferrer"
            title={verified?.error || link}
          >
            <span className="link-pill-title">{linkType}</span>
            <span className="link-pill-url">{link}</span>
            <span className="link-pill-status">{reachable === false ? "Unreachable" : "Open link"}</span>
          </a>
        );
      })}
    </div>
  );
}

async function uploadAndParseResume(file: File) {
  const contentType = file.type || (file.name.toLowerCase().endsWith(".docx") ? "application/vnd.openxmlformats-officedocument.wordprocessingml.document" : "application/pdf");

  const presignedRes = await fetch(`${API_BASE_URL}/resumes/upload-url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename: file.name, content_type: contentType }),
  });

  if (presignedRes.ok) {
    const pre = (await presignedRes.json()) as {
      reference_no: string;
      upload_url: string;
      s3_key: string;
    };

    const putRes = await fetch(pre.upload_url, {
      method: "PUT",
      body: file,
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
        filename: file.name,
        content_type: contentType,
        auto_parse: true,
      }),
    });

    if (!registerRes.ok) {
      const text = await registerRes.text();
      throw new Error(`register failed (${registerRes.status}) ${text}`);
    }

    const registered = (await registerRes.json()) as { reference_no: string; parsed_json?: ParsePayload };
    return {
      reference_no: registered.reference_no,
      parsed_json: registered.parsed_json,
      transport: "s3",
    };
  }

  const uploadForm = new FormData();
  uploadForm.append("resume", file);
  const directUploadRes = await fetch(`${API_BASE_URL}/resumes/upload`, {
    method: "POST",
    body: uploadForm,
  });

  if (!directUploadRes.ok) {
    const text = await directUploadRes.text();
    throw new Error(`upload failed (${directUploadRes.status}) ${text}`);
  }

  const uploaded = (await directUploadRes.json()) as { reference_no: string };
  const parseRes = await fetch(`${API_BASE_URL}/resumes/${uploaded.reference_no}/parse`, { method: "POST" });
  if (!parseRes.ok) {
    const text = await parseRes.text();
    throw new Error(`parse failed (${parseRes.status}) ${text}`);
  }

  return {
    reference_no: uploaded.reference_no,
    parsed_json: (await parseRes.json()) as ParsePayload,
    transport: "local",
  };
}

function HrPage(props: {
  hrOverview: HrOverview | null;
  loading: boolean;
  setLoading: (value: boolean) => void;
}) {
  const { hrOverview, loading, setLoading } = props;
  const [referenceNo, setReferenceNo] = useState("REF-001");
  const [candidateScore, setCandidateScore] = useState<CandidateScore | null>(null);
  const [scoreError, setScoreError] = useState("");

  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [uploadError, setUploadError] = useState("");
  const [parsePayload, setParsePayload] = useState<ParsePayload | null>(null);
  const [lastReferenceNo, setLastReferenceNo] = useState("");
  const [hrAiAnalysis, setHrAiAnalysis] = useState<HrAiAnalysis | null>(null);
  const [suitabilityResult, setSuitabilityResult] = useState<HrSuitabilityResponse | null>(null);
  const [suitabilityError, setSuitabilityError] = useState("");

  const [jobRole, setJobRole] = useState("Backend Engineer");
  const [mustHaveSkills, setMustHaveSkills] = useState("Python,Django,REST,SQL");
  const [techStack, setTechStack] = useState("Python,Django,PostgreSQL,Docker");
  const [niceToHaveSkills, setNiceToHaveSkills] = useState("Kubernetes,CI/CD,AWS");
  const [requiredExperienceYears, setRequiredExperienceYears] = useState("2");
  const [minFitScore, setMinFitScore] = useState("70");
  const [otherParams, setOtherParams] = useState("Strong API design, deployment familiarity, ownership mindset");
  const parsedLinks = useMemo(() => extractLinksFromParsedJson(parsePayload), [parsePayload]);

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

  const handleUploadAndParse = async () => {
    if (!resumeFile) {
      setUploadError("Select a PDF or DOCX file first.");
      return;
    }

    setLoading(true);
    setUploadError("");
    setUploadStatus("");
    setParsePayload(null);
    try {
      const result = await uploadAndParseResume(resumeFile);
      setUploadStatus(`Uploaded and parsed (${result.transport}). Reference: ${result.reference_no}`);
      setLastReferenceNo(result.reference_no);
      if (result.parsed_json) {
        setParsePayload(result.parsed_json);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Upload failed.";
      setUploadError(message);
    } finally {
      setLoading(false);
    }
  };

  const runHrAiAnalysis = async () => {
    const ref = (lastReferenceNo || referenceNo).trim();
    if (!ref) {
      setSuitabilityError("Provide a reference number or upload a resume first.");
      return;
    }

    setLoading(true);
    setSuitabilityError("");
    setHrAiAnalysis(null);
    try {
      const res = await fetch(`${API_BASE_URL}/candidates/${ref}/ai-analysis`);
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`AI analysis failed (${res.status}) ${text}`);
      }
      setHrAiAnalysis((await res.json()) as HrAiAnalysis);
    } catch (error) {
      const message = error instanceof Error ? error.message : "AI analysis failed.";
      setSuitabilityError(message);
    } finally {
      setLoading(false);
    }
  };

  const evaluateSuitability = async () => {
    const ref = (lastReferenceNo || referenceNo).trim();
    if (!ref) {
      setSuitabilityError("Provide a reference number or upload a resume first.");
      return;
    }

    setLoading(true);
    setSuitabilityError("");
    setSuitabilityResult(null);
    try {
      const res = await fetch(`${API_BASE_URL}/candidates/${ref}/ai-evaluation`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          role_name: jobRole,
          must_have_skills: mustHaveSkills,
          tech_stack: techStack,
          nice_to_have_skills: niceToHaveSkills,
          required_experience_years: requiredExperienceYears ? Number(requiredExperienceYears) : null,
          min_fit_score: minFitScore ? Number(minFitScore) : 70,
          other_parameters: otherParams,
        }),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Suitability check failed (${res.status}) ${text}`);
      }
      setSuitabilityResult((await res.json()) as HrSuitabilityResponse);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Suitability check failed.";
      setSuitabilityError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
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
              <p>Missing: {candidateScore.missing_skills.join(", ") || "None"}</p>
            </div>
          )}
        </article>

        <article className="card">
          <h3>Resume Upload + Parse</h3>
          <input type="file" accept=".pdf,.docx" onChange={(e) => setResumeFile(e.target.files?.[0] || null)} />
          <button onClick={handleUploadAndParse} type="button" disabled={loading}>
            Upload and Parse
          </button>
          {uploadStatus && <p className="ok">{uploadStatus}</p>}
          {uploadError && <p className="error">{uploadError}</p>}
          {parsePayload && (
            <div className="result">
              <p>
                Skills: <strong>{parsePayload.structured_profile.skills.join(", ") || "None"}</strong>
              </p>
              <p>
                Storage: {parsePayload.parse_meta.storage_backend} ({parsePayload.parse_meta.storage_key})
              </p>
              <p className="meta">Resume links</p>
              <LinkList links={parsedLinks.links} verifiedLinks={parsedLinks.verifiedLinks} />
            </div>
          )}
        </article>
      </div>

      <div className="card-grid">
        <article className="card">
          <h3>AI Analysis (HR View)</h3>
          <button type="button" onClick={runHrAiAnalysis} disabled={loading}>
            Get AI Analysis for Candidate
          </button>
          {hrAiAnalysis && (
            <div className="result">
              <p>
                <strong>Suggested roles:</strong> {(hrAiAnalysis.ai_analysis.job_roles || []).join(", ") || "None"}
              </p>
              <p className="meta">
                Provider: {hrAiAnalysis.provider || "unknown"} | Model: {hrAiAnalysis.model || "unknown"}
              </p>
            </div>
          )}
        </article>

        <article className="card">
          <h3>Job Suitability Parameters</h3>
          <label htmlFor="jobRole">Job role</label>
          <input id="jobRole" value={jobRole} onChange={(e) => setJobRole(e.target.value)} />

          <label htmlFor="mustHave">Must-have skills (comma separated)</label>
          <input id="mustHave" value={mustHaveSkills} onChange={(e) => setMustHaveSkills(e.target.value)} />

          <label htmlFor="techStack">Tech stack (comma separated)</label>
          <input id="techStack" value={techStack} onChange={(e) => setTechStack(e.target.value)} />

          <label htmlFor="niceToHave">Nice-to-have skills (comma separated)</label>
          <input id="niceToHave" value={niceToHaveSkills} onChange={(e) => setNiceToHaveSkills(e.target.value)} />

          <label htmlFor="requiredExp">Required experience years</label>
          <input id="requiredExp" value={requiredExperienceYears} onChange={(e) => setRequiredExperienceYears(e.target.value)} />

          <label htmlFor="minScore">Minimum fit score (0-100)</label>
          <input id="minScore" value={minFitScore} onChange={(e) => setMinFitScore(e.target.value)} />

          <label htmlFor="otherParams">Other parameters</label>
          <textarea id="otherParams" value={otherParams} onChange={(e) => setOtherParams(e.target.value)} />

          <button type="button" onClick={evaluateSuitability} disabled={loading}>
            Compare Resume JSONB and Evaluate
          </button>
        </article>
      </div>

      {suitabilityError && <p className="error">{suitabilityError}</p>}

      {suitabilityResult && (
        <div className="card">
          <h3>Suitability Decision</h3>
          <div className="result">
            <p>
              <strong>Decision:</strong> {suitabilityResult.comparison?.decision || "UNKNOWN"}
            </p>
            <p>
              <strong>Resume suitable:</strong> {suitabilityResult.comparison?.is_resume_suitable ? "Yes" : "No"}
            </p>
            <p>
              <strong>Fit score:</strong> {suitabilityResult.comparison?.fit_score ?? 0} / threshold {suitabilityResult.evaluation_input?.min_fit_score ?? 70}
            </p>
            <p>
              <strong>Fit threshold passed:</strong> {suitabilityResult.comparison?.fit_threshold_passed ? "Yes" : "No"}
            </p>
            <p>
              <strong>Experience threshold passed:</strong> {suitabilityResult.comparison?.experience_threshold_passed ? "Yes" : "No"}
            </p>

            {!!suitabilityResult.ai_evaluation?.strengths?.length && (
              <>
                <h4>Strengths</h4>
                <ul>
                  {suitabilityResult.ai_evaluation.strengths.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </>
            )}

            {!!suitabilityResult.ai_evaluation?.gaps?.length && (
              <>
                <h4>Gaps</h4>
                <ul>
                  {suitabilityResult.ai_evaluation.gaps.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </>
            )}

            {!!suitabilityResult.ai_evaluation?.recommendations?.length && (
              <>
                <h4>Recommendations</h4>
                <ul>
                  {suitabilityResult.ai_evaluation.recommendations.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </>
            )}

            <p className="meta">
              Provider: {suitabilityResult.provider || "unknown"} | Model: {suitabilityResult.model || "unknown"}
            </p>
          </div>
        </div>
      )}
    </section>
  );
}

function StudentPage(props: {
  studentOverview: StudentOverview | null;
  loading: boolean;
  setLoading: (value: boolean) => void;
}) {
  const { studentOverview, loading, setLoading } = props;
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState("");
  const [uploadStatus, setUploadStatus] = useState("");
  const [referenceNo, setReferenceNo] = useState("");
  const [parsePayload, setParsePayload] = useState<ParsePayload | null>(null);
  const [roleAnalysis, setRoleAnalysis] = useState<AiRoleAnalysisPayload | null>(null);
  const [roleSkills, setRoleSkills] = useState<RoleSkillView[]>([]);
  const [careerPlan, setCareerPlan] = useState<CareerRecommendationPayload | null>(null);
  const parsedLinks = useMemo(() => extractLinksFromParsedJson(parsePayload), [parsePayload]);

  const uniqueMissingSkills = useMemo(() => {
    const bag = new Set<string>();
    roleSkills.forEach((r) => r.missing_skills.forEach((s) => bag.add(s)));
    return [...bag];
  }, [roleSkills]);

  const runAiPathAnalysis = async (ref: string) => {
    const analysisRes = await fetch(`${API_BASE_URL}/candidates/${ref}/ai-analysis`);
    if (!analysisRes.ok) {
      throw new Error("ai-analysis failed");
    }
    const analysis = (await analysisRes.json()) as AiRoleAnalysisPayload;
    const roles = analysis.ai_analysis?.job_roles || [];

    const roleScoreViews = await Promise.all(
      roles.slice(0, 5).map(async (role) => {
        const scoreRes = await fetch(`${API_BASE_URL}/candidates/${ref}/score?role=${encodeURIComponent(role)}`);
        if (!scoreRes.ok) {
          return {
            role,
            matched_skills: [],
            missing_skills: [],
            score_normalized: 0,
          } as RoleSkillView;
        }
        const payload = (await scoreRes.json()) as CandidateScore;
        return {
          role,
          matched_skills: payload.matched_skills || [],
          missing_skills: payload.missing_skills || [],
          score_normalized: payload.score_normalized || 0,
        } as RoleSkillView;
      }),
    );

    const recommendationRes = await fetch(`${API_BASE_URL}/candidates/${ref}/career-recommendations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_roles: roles }),
    });

    const recommendations = recommendationRes.ok
      ? ((await recommendationRes.json()) as CareerRecommendationPayload)
      : null;

    setRoleAnalysis(analysis);
    setRoleSkills(roleScoreViews);
    setCareerPlan(recommendations);
  };

  const handleUploadAndAnalyze = async () => {
    if (!resumeFile) {
      setUploadError("Select a PDF or DOCX file first.");
      return;
    }

    setLoading(true);
    setUploadError("");
    setUploadStatus("");
    setRoleAnalysis(null);
    setRoleSkills([]);
    setCareerPlan(null);
    try {
      const result = await uploadAndParseResume(resumeFile);
      setReferenceNo(result.reference_no);
      setParsePayload(result.parsed_json || null);
      await runAiPathAnalysis(result.reference_no);
      setUploadStatus(`Student resume analyzed. Reference: ${result.reference_no}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Student analysis failed.";
      setUploadError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel">
      <h2>{studentOverview?.title || "Student Career Page"}</h2>
      <p>{studentOverview?.description || "Upload your resume and get AI-driven role paths, growth roadmap, and missing-skill guidance."}</p>

      <div className="card-grid">
        <article className="card">
          <h3>Student Resume Upload</h3>
          <input type="file" accept=".pdf,.docx" onChange={(e) => setResumeFile(e.target.files?.[0] || null)} />
          <button type="button" onClick={handleUploadAndAnalyze} disabled={loading}>
            Upload and Get Path Analysis
          </button>
          {uploadStatus && <p className="ok">{uploadStatus}</p>}
          {uploadError && <p className="error">{uploadError}</p>}
          {referenceNo && <p className="meta">Reference: {referenceNo}</p>}
          {parsePayload && (
            <div className="result">
              <p>
                Current skills: <strong>{parsePayload.structured_profile.skills.join(", ") || "None"}</strong>
              </p>
            </div>
          )}
        </article>

        <article className="card">
          <h3>AI Role Paths</h3>
          {!roleAnalysis && <p className="meta">No AI path analysis yet.</p>}
          {roleAnalysis && (
            <div className="result">
              <ul>
                {roleAnalysis.ai_analysis.job_roles.map((role) => (
                  <li key={role}>{role}</li>
                ))}
              </ul>
              <p className="meta">
                Provider: {roleAnalysis.provider || "unknown"} | Model: {roleAnalysis.model || "unknown"}
              </p>
            </div>
          )}
        </article>
      </div>

      {parsePayload && (
        <article className="card">
          <h3>Resume Links</h3>
          <p className="meta">Links loaded from the parsed record in the database.</p>
          <LinkList links={parsedLinks.links} verifiedLinks={parsedLinks.verifiedLinks} />
        </article>
      )}

      <div className="card-grid">
        <article className="card">
          <h3>Missing Skills by Path</h3>
          {!roleSkills.length && <p className="meta">Upload and analyze resume to see missing skills.</p>}
          {!!roleSkills.length && (
            <div className="result">
              <div className="path-grid">
                {roleSkills.map((roleView) => (
                  <div key={roleView.role} className="path-card">
                    <p>
                      <strong>{roleView.role}</strong> - Fit {toPercent(roleView.score_normalized)}
                    </p>
                    <p>Missing: {roleView.missing_skills.join(", ") || "None"}</p>
                    <p>Matched: {roleView.matched_skills.join(", ") || "None"}</p>
                  </div>
                ))}
              </div>
              <p>
                <strong>Priority skill gaps:</strong> {uniqueMissingSkills.join(", ") || "None"}
              </p>
            </div>
          )}
        </article>

        <article className="card">
          <h3>Growth Roadmap</h3>
          {!careerPlan?.recommendations && <p className="meta">No roadmap available yet.</p>}
          {careerPlan?.recommendations && (
            <div className="result">
              {Object.entries(careerPlan.recommendations.skill_roadmap || {}).map(([phase, items]) => (
                <div key={phase} className="roadmap-line">
                  <p>
                    <strong>{phase}</strong>: {(items || []).join(", ")}
                  </p>
                </div>
              ))}
              <p>
                <strong>Estimated growth timeline:</strong> {careerPlan.recommendations.timeline || "Not available"}
              </p>
            </div>
          )}
        </article>
      </div>
    </section>
  );
}

function AdminPage(props: {
  adminOverview: AdminOverview | null;
  loading: boolean;
  setLoading: (value: boolean) => void;
}) {
  const { adminOverview, loading, setLoading } = props;
  const [liveAdminOverview, setLiveAdminOverview] = useState<AdminOverview>(adminOverview ?? DEFAULT_ADMIN_OVERVIEW);
  const [adminValidationText, setAdminValidationText] = useState("This profile has no private contact details.");
  const [adminValidationResult, setAdminValidationResult] = useState("");
  const [adminUsername, setAdminUsername] = useState("");
  const [adminPassword, setAdminPassword] = useState("");
  const [adminToken, setAdminToken] = useState(localStorage.getItem("gethired_admin_session_token") || "");
  const [adminLoginError, setAdminLoginError] = useState("");
  const [recordsPayload, setRecordsPayload] = useState<AdminRecordListResponse | null>(null);
  const [selectedRef, setSelectedRef] = useState("");
  const [recordDetail, setRecordDetail] = useState<AdminRecordDetailResponse | null>(null);
  const [recordsError, setRecordsError] = useState("");
  const recordLinks = useMemo(() => extractLinksFromParsedJson(recordDetail?.parsed_json), [recordDetail]);

  const authHeaders: Record<string, string> = adminToken
    ? { "X-Session-Token": adminToken }
    : {};

  useEffect(() => {
    if (!adminToken) {
      setLiveAdminOverview(adminOverview ?? DEFAULT_ADMIN_OVERVIEW);
      return;
    }

    let cancelled = false;
    const loadAdminOverview = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/admin`, {
          headers: { ...authHeaders },
        });
        if (!res.ok) {
          return;
        }
        const payload = (await res.json()) as AdminOverview;
        if (!cancelled) {
          setLiveAdminOverview(payload);
        }
      } catch {
        if (!cancelled) {
          setLiveAdminOverview(adminOverview ?? DEFAULT_ADMIN_OVERVIEW);
        }
      }
    };

    void loadAdminOverview();

    return () => {
      cancelled = true;
    };
  }, [adminToken, adminOverview]);

  const loginAdmin = async () => {
    setLoading(true);
    setAdminLoginError("");
    try {
      const res = await fetch("http://127.0.0.1:8000/_allauth/app/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: adminUsername, password: adminPassword }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Admin login failed (${res.status}) ${text}`);
      }

      const payload = (await res.json()) as {
        meta?: { session_token?: string };
        data?: { user?: { username?: string } };
      };

      const sessionToken = payload.meta?.session_token;
      if (!sessionToken) {
        throw new Error("Headless login did not return session token.");
      }

      localStorage.setItem("gethired_admin_session_token", sessionToken);
      setAdminToken(sessionToken);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Admin login failed.";
      setAdminLoginError(message);
    } finally {
      setLoading(false);
    }
  };

  const logoutAdmin = () => {
    localStorage.removeItem("gethired_admin_session_token");
    setAdminToken("");
    setRecordsPayload(null);
    setRecordDetail(null);
    setSelectedRef("");
  };

  const loadAllRecords = async () => {
    if (!adminToken) {
      setRecordsError("Login as admin first.");
      return;
    }
    setLoading(true);
    setRecordsError("");
    try {
      const res = await fetch(`${API_BASE_URL}/admin/records`, {
        headers: { ...authHeaders },
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Load records failed (${res.status}) ${text}`);
      }
      setRecordsPayload((await res.json()) as AdminRecordListResponse);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load admin records.";
      setRecordsError(message);
      setRecordsPayload(null);
    } finally {
      setLoading(false);
    }
  };

  const loadRecordDetail = async (referenceNo: string) => {
    if (!adminToken) {
      setRecordsError("Login as admin first.");
      return;
    }
    if (!referenceNo.trim()) {
      setRecordsError("Select or enter a reference number.");
      return;
    }

    setLoading(true);
    setRecordsError("");
    try {
      const res = await fetch(`${API_BASE_URL}/admin/records/${referenceNo.trim()}`, {
        headers: { ...authHeaders },
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Load record detail failed (${res.status}) ${text}`);
      }
      setRecordDetail((await res.json()) as AdminRecordDetailResponse);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load record detail.";
      setRecordsError(message);
      setRecordDetail(null);
    } finally {
      setLoading(false);
    }
  };

  const runAdminValidation = async () => {
    if (!adminToken) {
      setAdminValidationResult("Login as admin first.");
      return;
    }

    setLoading(true);
    setAdminValidationResult("");
    try {
      const res = await fetch(`${API_BASE_URL}/privacy/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders },
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
    <section className="panel">
      <h2>{liveAdminOverview.title}</h2>
      <p>{liveAdminOverview.description}</p>

      <div className="card-grid">
        <article className="card">
          <h3>Admin Login (Superuser)</h3>
          <label htmlFor="adminUsername">Username</label>
          <input id="adminUsername" value={adminUsername} onChange={(e) => setAdminUsername(e.target.value)} />
          <label htmlFor="adminPassword">Password</label>
          <input id="adminPassword" type="password" value={adminPassword} onChange={(e) => setAdminPassword(e.target.value)} />
          <button type="button" onClick={loginAdmin} disabled={loading}>
            Login
          </button>
          <button type="button" onClick={logoutAdmin} disabled={loading || !adminToken}>
            Logout
          </button>
          {adminToken && <p className="ok">Admin authenticated.</p>}
          {adminLoginError && <p className="error">{adminLoginError}</p>}
        </article>

        <article className="card">
          <h3>Parsed Records Explorer</h3>
          <button type="button" onClick={loadAllRecords} disabled={loading || !adminToken}>
            Load All Parsed Records
          </button>
          <label htmlFor="selectedRef">Reference number</label>
          <input id="selectedRef" value={selectedRef} onChange={(e) => setSelectedRef(e.target.value)} placeholder="REF-XXXXXXXX" />
          <button type="button" onClick={() => void loadRecordDetail(selectedRef)} disabled={loading || !adminToken}>
            Load Full Record Detail
          </button>
          {recordsError && <p className="error">{recordsError}</p>}
          {recordsPayload && (
            <div className="result">
              <p>
                <strong>Total records:</strong> {recordsPayload.count}
              </p>
              <ul>
                {recordsPayload.results.slice(0, 30).map((item) => (
                  <li key={item.reference_no}>
                    <button type="button" className="inline-link" onClick={() => {
                      setSelectedRef(item.reference_no);
                      void loadRecordDetail(item.reference_no);
                    }}>
                      {item.reference_no}
                    </button>
                    {` | ${item.status} | roles: ${(item.roles || []).join(", ") || "None"} | skills: ${(item.skills || []).length}`}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </article>
      </div>

      {recordDetail && (
        <article className="card">
          <h3>Full Parsed JSONB + AI Cache</h3>
          <div className="result">
            <p>
              <strong>Reference:</strong> {recordDetail.reference_no}
            </p>
            <p>
              <strong>File:</strong> {recordDetail.original_filename} ({recordDetail.content_type})
            </p>
            <p>
              <strong>Status:</strong> {recordDetail.status}
            </p>
            <pre className="json-view">{JSON.stringify(recordDetail.parsed_json, null, 2)}</pre>
          </div>
        </article>
      )}

      {recordDetail && (
        <article className="card">
          <h3>Resume Links</h3>
          <p className="meta">Links loaded from the saved record in the database.</p>
          <LinkList links={recordLinks.links} verifiedLinks={recordLinks.verifiedLinks} />
        </article>
      )}

      <div className="card-grid">
        <article className="card">
          <h3>Governance Metrics</h3>
          <p>Audit target: {liveAdminOverview.metrics.deanonymize_audit_target}</p>
          <p>DIR threshold: {liveAdminOverview.metrics.fairness_dir_threshold}</p>
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
  );
}

function App() {
  const [hrOverview, setHrOverview] = useState<HrOverview | null>(null);
  const [studentOverview, setStudentOverview] = useState<StudentOverview | null>(null);
  const [adminOverview] = useState<AdminOverview | null>(null);
  const [overviewError, setOverviewError] = useState("");

  const [loading, setLoading] = useState(false);

  const portalHighlights = useMemo(
    () => [
      {
        label: "HR candidates",
        value: String(hrOverview?.candidate_refs?.length ?? 0),
        note: "candidate references ready",
      },
      {
        label: "Student path",
        value: studentOverview ? "Live" : "Loading",
        note: "AI guidance and roadmap",
      },
      {
        label: "Admin access",
        value: "Protected",
        note: "session token required",
      },
    ],
    [hrOverview, studentOverview],
  );

  useEffect(() => {
    const loadOverviews = async () => {
      setOverviewError("");
      try {
        const [hrRes, studentRes] = await Promise.all([
          fetch(`${API_BASE_URL}/hr`),
          fetch(`${API_BASE_URL}/student`),
        ]);
        if (!hrRes.ok || !studentRes.ok) {
          throw new Error("overview endpoints unavailable");
        }

        const hrData = (await hrRes.json()) as HrOverview;
        const studentData = (await studentRes.json()) as StudentOverview;

        setHrOverview(hrData);
        setStudentOverview(studentData);
      } catch {
        setOverviewError("Failed to load role pages from backend endpoints.");
      }
    };

    void loadOverviews();
  }, []);

  return (
    <BrowserRouter>
      <div className="shell">
        <header className="masthead">
          <div className="masthead-copy">
            <p className="tag">GetHired v2</p>
            <h1>Role-Specific Portal</h1>
            <p className="masthead-lead">A sharper workspace for recruiter scoring, student career planning, and admin governance workflows.</p>
          </div>

          <div className="hero-grid" aria-label="portal highlights">
            {portalHighlights.map((item) => (
              <article className="hero-card" key={item.label}>
                <p className="hero-label">{item.label}</p>
                <p className="hero-value">{item.value}</p>
                <p className="hero-note">{item.note}</p>
              </article>
            ))}
          </div>
        </header>

        <nav className="role-nav" aria-label="role navigation">
          <NavLink className={({ isActive }) => `route-link${isActive ? " active" : ""}`} to="/hr">
            HR Page
          </NavLink>
          <NavLink className={({ isActive }) => `route-link${isActive ? " active" : ""}`} to="/student">
            Student Page
          </NavLink>
          <NavLink className={({ isActive }) => `route-link${isActive ? " active" : ""}`} to="/admin">
            Admin Page
          </NavLink>
        </nav>

        {overviewError && <p className="error">{overviewError}</p>}

        <Routes>
          <Route path="/" element={<Navigate to="/hr" replace />} />
          <Route path="/hr" element={<HrPage hrOverview={hrOverview} loading={loading} setLoading={setLoading} />} />
          <Route path="/student" element={<StudentPage studentOverview={studentOverview} loading={loading} setLoading={setLoading} />} />
          <Route path="/admin" element={<AdminPage adminOverview={adminOverview} loading={loading} setLoading={setLoading} />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
