# Google Gemini AI Integration Guide

## Overview

GetHired now includes AI-powered candidate evaluation and resume analysis using Google's Gemini API. This enables:

1. **AI-Powered Candidate Evaluation**: Score candidates against specific job roles and skill requirements
2. **Deep Resume Analysis**: AI-generated professional insights and career assessment
3. **Personalized Career Recommendations**: Learning paths and skill development guidance

## Setup Instructions

### 1. Get Google Gemini API Key

1. Go to [Google AI Studio (Makersuite)](https://makersuite.google.com/app/apikey)
2. Click **"Create API Key"**
3. Copy your API key (keep it secure!)
4. You'll get an API key that looks like: `AIzaSy...xxxxx`

### 2. Configure Environment Variables

Edit `.env` and add:

```env
GEMINI_API_KEY=YOUR_API_KEY_HERE
GEMINI_ENABLED=True
```

Replace `YOUR_API_KEY_HERE` with your actual API key.

### 3. Verify Installation

Check that Gemini is enabled:

```bash
curl http://127.0.0.1:8003/api/v1/ai/status
```

Expected response:
```json
{
  "gemini_enabled": true,
  "status": "ready",
  "message": "Gemini AI is configured and ready."
}
```

## API Endpoints

### 1. Candidate AI Evaluation

**Endpoint**: `POST /api/v1/candidates/{reference_no}/ai-evaluation`

Evaluate a candidate for a specific job role using their extracted resume skills.

**Request Body**:
```json
{
  "job_description": "Senior Backend Engineer with 5+ years of Python and PostgreSQL experience",
  "required_skills": ["Python", "Django", "REST", "SQL", "Docker"]
}
```

**Response**:
```json
{
  "status": "success",
  "reference_no": "REF-17996561",
  "ai_evaluation": {
    "fit_score": 85,
    "strengths": [
      "Strong Python background with Django framework expertise",
      "Demonstrated SQL and database experience",
      "Full-stack capabilities enabling backend work"
    ],
    "gaps": [
      "Limited explicit Docker/containerization experience",
      "No mention of advanced PostgreSQL optimization"
    ],
    "recommendations": [
      "Complete Docker fundamentals course (2-3 weeks)",
      "Study PostgreSQL performance tuning (4-6 weeks)"
    ],
    "confidence": "high",
    "reasoning": "Candidate has core backend skills; gaps are specific tooling that can be quickly acquired."
  },
  "model": "gemini-pro"
}
```

### 2. Resume AI Analysis

**Endpoint**: `GET /api/v1/candidates/{reference_no}/ai-analysis`

Deep-dive analysis of candidate profile and career trajectory.

**Response**:
```json
{
  "status": "success",
  "reference_no": "REF-17996561",
  "ai_analysis": {
    "summary": "Software engineer with diverse full-stack experience spanning multiple programming languages and platforms. Demonstrates practical project development and learning commitment.",
    "strengths": [
      "Multi-disciplinary technical foundation",
      "Practical project portfolio",
      "Willingness to learn new technologies"
    ],
    "trajectory": "Early-career developer building foundational skills across multiple domains",
    "opportunities": [
      "Specialize in a specific domain (backend/frontend/DevOps)",
      "Deepen expertise in one technology stack",
      "Contribute to larger-scale collaborative projects"
    ],
    "career_stage": "Junior"
  },
  "model": "gemini-pro"
}
```

### 3. Career Recommendations

**Endpoint**: `POST /api/v1/candidates/{reference_no}/career-recommendations`

Generate personalized learning and career development paths.

**Request Body**:
```json
{
  "target_roles": ["Backend Engineer", "Senior Backend Engineer"]
}
```

**Response**:
```json
{
  "status": "success",
  "reference_no": "REF-17996561",
  "recommendations": {
    "skill_roadmap": {
      "month_1_2": ["PostgreSQL advanced queries", "Docker containerization"],
      "month_3_4": ["System design fundamentals", "Kubernetes basics"],
      "month_5_6": ["Microservices architecture", "CI/CD pipelines"]
    },
    "certifications": [
      "Google Cloud Associate Cloud Engineer",
      "AWS Solutions Architect Associate"
    ],
    "projects": [
      "Build a scalable REST API with authentication",
      "Deploy multi-container application with Docker Compose",
      "Implement CI/CD pipeline with GitHub Actions"
    ],
    "community": [
      "Join Python/Django developer community",
      "Contribute to open-source backend projects",
      "Participate in backend design discussions"
    ],
    "timeline": "6-9 months to Senior Backend Engineer readiness"
  },
  "target_roles": ["Backend Engineer", "Senior Backend Engineer"],
  "model": "gemini-pro"
}
```

## Usage Examples

### Example 1: Evaluate Candidate for Backend Role

```bash
curl -X POST http://127.0.0.1:8003/api/v1/candidates/REF-17996561/ai-evaluation \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Backend Engineer: Build scalable REST APIs using Python/Django with PostgreSQL. Experience with Docker required.",
    "required_skills": ["Python", "Django", "REST", "SQL", "Docker"]
  }'
```

### Example 2: Get Resume Analysis

```bash
curl http://127.0.0.1:8003/api/v1/candidates/REF-17996561/ai-analysis
```

### Example 3: Get Career Development Path

```bash
curl -X POST http://127.0.0.1:8003/api/v1/candidates/REF-17996561/career-recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "target_roles": ["Backend Engineer", "DevOps Engineer", "Senior Backend Engineer"]
  }'
```

## Features Integrated

### 1. Role-Relevant Skill Extraction

The parser now identifies job-relevant skills based on extracted roles:

```json
"job_relevant_skills": {
  "role_requirements": {
    "Software Engineer": ["Python", "SQL", "Git", "REST"]
  },
  "matched": ["Python", "SQL", "Git", "REST"],
  "missing": []
}
```

### 2. Candidate Score Endpoint Enhancement

The existing `/api/v1/candidates/{reference_no}/score` endpoint now uses extracted skills:

```bash
curl http://127.0.0.1:8003/api/v1/candidates/REF-17996561/score?role=backend%20engineer
```

Response shows matched and missing skills for the specified role.

### 3. Structured Education Output

Education now includes institution, degree, and year_range in structured format for better candidate profiling.

## Environment Variables Reference

```env
# Google Gemini AI Configuration
GEMINI_API_KEY=AIzaSy...xxxxx          # Your Google API key
GEMINI_ENABLED=True                    # Enable/disable AI features
```

## Cost Considerations

- Google Gemini API is **free for development** with reasonable rate limits
- Check [Google AI Pricing](https://ai.google.dev/pricing) for production usage
- Rate limits: Generous tier includes 15 requests per minute for free usage

## Troubleshooting

### API Key Not Recognized

```
Error: Gemini AI is not configured.
Fix: Ensure GEMINI_API_KEY is set in .env and contains a valid key
```

### Rate Limit Exceeded

```
Error: Resource has been exhausted
Fix: Wait a minute before retrying, or upgrade to paid tier
```

### JSON Parsing Error

If AI response cannot be parsed as JSON, the endpoint returns raw response for debugging.

## Next Steps

1. Get your Gemini API key from [Makersuite](https://makersuite.google.com/app/apikey)
2. Add it to `.env` and set `GEMINI_ENABLED=True`
3. Test with the status endpoint to confirm it's working
4. Use the evaluation endpoints to assess candidate fit for your roles

## Documentation Links

- [Google Generative AI Python SDK](https://github.com/google/generative-ai-python)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [GetHired Resume Parser](/md/PHASE1_IMPLEMENTATION.md)
