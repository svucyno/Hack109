# Smart AI Fallback System - Complete Setup Guide

## Overview

The **Smart AI Fallback System** implements a resilient, multi-provider evaluation framework that gracefully degrades when primary AI providers are unavailable.

### Provider Chain (Executed Sequentially)
1. **Google Gemini (Primary)** - Free tier with rate limits; handles most requests when quota allows
2. **OpenRouter (Fallback)** - Paid but reliable; activated when Gemini is rate-limited
3. **Rule-Based Evaluation (Last Resort)** - Pure skill matching; always available

---

## Architecture

### Smart Inference Module (`core/smart_inference.py`)

Three main entry points automatically try the provider chain:

```python
from core.smart_inference import (
    smart_evaluate_candidate,      # For job role fit scoring
    smart_analyze_resume,          # For resume deep-dive analysis
    smart_generate_recommendations # For career path recommendations
)
```

### Response Structure (Consistent Across Providers)

All three functions return:
```json
{
  "status": "success",
  "reference_no": "REF-XXXXXXXX",
  "provider": "gemini|openrouter|fallback",
  "fallback_used": false,
  "fallback_reason": "[optional: why fallback triggered]",
  "ai_evaluation": { ... },
  "model": "gemini-2.0-flash|openai/gpt-4o-mini|rule-based"
}
```

---

## Setup Instructions

### Step 1: Verify Gemini Configuration (Already Done)

Check `.env`:
```bash
GEMINI_API_KEY=AIzaSyA...  # ✅ Should be populated
GEMINI_ENABLED=True
```

Test current status:
```bash
curl http://127.0.0.1:8000/api/v1/ai/status
```

Expected with just Gemini:
```json
{
  "gemini_enabled": true,
  "openrouter_enabled": false,
  "available_providers": ["gemini"],
  "status": "ready",
  "fallback_enabled": false
}
```

### Step 2: Get OpenRouter API Key (Free Tier Available)

**Option A: One-time setup (recommended for testing)**
1. Visit https://openrouter.ai/
2. Sign up (free) → https://openrouter.ai/auth/signup
3. Go to Settings → Create new API key
4. Copy the key

**Option B: Production account (recommended for long-term)**
1. Create account
2. Set up billing (credits-based, $5 minimum)
3. Create API key with spend limits

**Free tier limitations:**
- 100,000 free tokens per month across all models
- Sufficient for ~50-100 full evaluations
- After free tier: Standard pricing (typically $0.50-$2 per 1M tokens)

### Step 3: Configure OpenRouter in `.env`

Add/update in `.env`:
```bash
OPENROUTER_API_KEY=sk-or-v1-...      # Your API key from Step 2
OPENROUTER_ENABLED=True
OPENROUTER_MODEL=openai/gpt-4o-mini  # Options: see below
```

**Alternative OpenRouter Models** (by performance/cost):

```
# Recommended (cost-optimized)
openai/gpt-4o-mini        # Fast, good quality, cheapest
anthropic/claude-3-haiku  # Fast, compact, ultra-cheap

# Mid-tier (better quality)
openai/gpt-4-turbo        # High quality, higher cost
anthropic/claude-3-sonnet # Balanced quality/cost

# Premium (best quality)
anthropic/claude-3-opus   # Highest quality, expensive
openai/gpt-4              # Most capable, most expensive
```

### Step 4: Validate Configuration

Restart the Django development server:
```bash
# Stop current server (Ctrl+C)

# Restart with:
uv run manage.py runserver 8000
```

Check status endpoint again:
```bash
curl http://127.0.0.1:8000/api/v1/ai/status
```

Expected with both providers:
```json
{
  "gemini_enabled": true,
  "openrouter_enabled": true,
  "available_providers": ["gemini", "openrouter"],
  "status": "ready",
  "fallback_enabled": true,
  "message": "Multiple providers available"
}
```

---

## Usage Examples

### Example 1: Automatic Fallback (Most Common)

When Gemini rate-limits, system auto-switches to OpenRouter:

```bash
# First request → Tries Gemini (will work if quota available)
curl -X POST http://127.0.0.1:8000/api/v1/candidates/REF-123/ai-evaluation \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Senior Backend Engineer with Python/Django",
    "required_skills": ["Python", "Django", "REST", "SQL"]
  }'

# Response includes:
# {
#   "provider": "gemini",
#   "fallback_used": false,
#   "ai_evaluation": { ... }
# }

# After Gemini rate-limited (usually after 10-15 requests on free tier):
# → System automatically uses OpenRouter for next requests

# Response includes:
# {
#   "provider": "openrouter",
#   "fallback_used": true,
#   "fallback_reason": "Gemini rate-limited",
#   "ai_evaluation": { ... }
# }

# If both fail or disabled, uses rule-based:
# {
#   "provider": "fallback",
#   "model": "rule-based",
#   "ai_evaluation": { ... },
#   "fallback_used": true
# }
```

### Example 2: Candidate Evaluation

```bash
curl -X POST http://127.0.0.1:8000/api/v1/candidates/REF-17996561/ai-evaluation \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Backend engineer - Python, FastAPI, PostgreSQL, Docker",
    "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Git"]
  }'
```

Response (auto-selects best available provider):
```json
{
  "status": "success",
  "reference_no": "REF-17996561",
  "provider": "gemini",
  "fallback_used": false,
  "ai_evaluation": {
    "fit_score": 92,
    "strengths": [
      "Strong Python expertise with multiple years of professional experience",
      "Proven FastAPI adoption and REST API design",
      "Database optimization skills transferable to PostgreSQL"
    ],
    "gaps": [
      "Limited explicit Docker containerization experience",
      "No mention of orchestration tools"
    ],
    "recommendations": [
      "Take 2-week Docker & containerization course",
      "Build production Docker+Kubernetes project",
      "Practice multi-container orchestration"
    ]
  },
  "model": "gemini-2.0-flash"
}
```

### Example 3: Resume Deep-Dive Analysis

```bash
curl -X GET http://127.0.0.1:8000/api/v1/candidates/REF-17996561/ai-analysis
```

Response (auto-selects best provider):
```json
{
  "status": "success",
  "ai_analysis": {
    "summary": "Mid-level full-stack engineer with strong backend prowess and emerging frontend capabilities. 5+ years professional experience, primarily Python/Django ecosystem.",
    "strengths": [
      "Deep backend expertise in Python/Django",
      "SQL optimization and database design skills",
      "API design and REST principles mastery",
      "Leading team projects and architecture decisions"
    ],
    "trajectory": "Advancing toward senior backend leadership role or architect track",
    "opportunities": [
      "Specialize in system design and scalability",
      "Explore cloud-native architectures (Kubernetes, serverless)",
      "Mentor junior developers and lead architecture decisions"
    ],
    "career_stage": "Mid"
  },
  "provider": "gemini"
}
```

### Example 4: Career Recommendations

```bash
curl -X POST http://127.0.0.1:8000/api/v1/candidates/REF-17996561/career-recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "target_roles": ["Senior Backend Engineer", "DevOps Engineer", "Solutions Architect"]
  }'
```

Response (auto-selects best provider):
```json
{
  "status": "success",
  "recommendations": {
    "skill_roadmap": {
      "month_1_2": ["Kubernetes fundamentals", "Terraform for IaC"],
      "month_3_4": ["AWS Solutions Architect cert", "System design deep-dive"],
      "month_5_6": ["Lead infrastructure project", "DevOps mentoring"]
    },
    "certifications": [
      "AWS Solutions Architect Associate",
      "Certified Kubernetes Administrator"
    ],
    "projects": [
      "Build and deploy microservices to Kubernetes",
      "Design multi-region disaster recovery setup",
      "Optimize cloud infrastructure costs by 40%"
    ],
    "community": [
      "Join DevOps/SRE slack communities",
      "Write infrastructure blog posts",
      "Speak at infrastructure meetups"
    ],
    "timeline": "6-9 months to reach target role"
  },
  "target_roles": ["Senior Backend Engineer", "DevOps Engineer", "Solutions Architect"],
  "provider": "gemini"
}
```

---

## Monitoring Provider Usage

### Quick Status Check
```bash
curl http://127.0.0.1:8000/api/v1/ai/status
```

### Understanding Response Codes

| Status | Meaning | Action |
|--------|---------|--------|
| 200 OK | Successful evaluation | Response contains AI analysis |
| 429 (From Gemini) | Gemini rate-limited | System auto-falls back to OpenRouter |
| 503 Service Unavailable | No providers configured | Set GEMINI_API_KEY or OPENROUTER_API_KEY in .env |
| 404 Not Found | Resume not parsed yet | Upload and parse resume first |

### Observing Fallback Behavior

When multiple providers are configured, you'll see in responses:

**Gemini available:**
```json
{"provider": "gemini", "fallback_used": false}
```

**Gemini quota exhausted, OpenRouter used:**
```json
{
  "provider": "openrouter",
  "fallback_used": true,
  "fallback_reason": "Gemini rate-limited or unavailable"
}
```

**Both unavailable, rule-based used:**
```json
{
  "provider": "fallback",
  "fallback_used": true,
  "model": "rule-based",
  "reasoning": "AI providers unavailable; using skill matching"
}
```

---

## Cost Management

### Estimating Costs

**Gemini Cost:** FREE (100k requests/month free tier)
- Sufficient for: ~50-100 full candidate evaluations

**OpenRouter Cost** (when Gemini exhausted):
- **gpt-4o-mini:** ~$0.00015 per 1K tokens → ~$0.10-$0.20 per evaluation
- **claude-3-haiku:** ~$0.00008 per 1K tokens → ~$0.05-$0.10 per evaluation
- **Monthly budget (100 evaluations):** $5-$20

### Setting Spend Limits

On OpenRouter dashboard:
1. Settings → Usage & Quotas
2. Set monthly spend limit (e.g., $20)
3. Requests rejected gracefully when limit reached
4. System falls back to rule-based evaluation

### Optimizing Costs

1. **Use Gemini for high-volume:** Free up to quota
2. **Cache results:** Same candidate + job = cached response (TODO: implement)
3. **Use cheaper models:** claude-3-haiku instead of gpt-4o-mini
4. **Batch evaluations:** Off-peak times if possible

---

## Troubleshooting

### Problem: Status shows `openrouter_enabled: false` but API key is set

**Solution:**
```bash
# 1. Verify .env has newline at end
# 2. Restart server:
uv run manage.py runserver 8000

# 3. Check env load:
python -c "from django.conf import settings; print(settings.OPENROUTER_ENABLED)"
```

### Problem: Getting rule-based evaluation instead of AI

**Check provider status:**
```bash
curl http://127.0.0.1:8000/api/v1/ai/status
```

If `available_providers: []`:
- Set GEMINI_API_KEY or OPENROUTER_API_KEY in .env
- Restart server

If providers available but getting fallback:
- Gemini quota exhausted (check free tier usage in Google Cloud Console)
- OpenRouter API key invalid (test with curl directly)
- Both providers experiencing issues (retry in a few minutes)

### Problem: OpenRouter returning 401 Unauthorized

**Solution:**
```bash
# Verify API key format:
# - Should start with: sk-or-v1-
# - Get fresh key from: https://openrouter.ai/auth/keys

# Test key directly:
curl -X POST "https://openrouter.ai/api/v1/chat/completions" \
  -H "Authorization: Bearer sk-or-v1-YOUR_KEY_HERE" \
  -H "HTTP-Referer: http://localhost:8000" \
  -H "X-OpenRouter-Title: GetHired" \
  -H "Content-Type: application/json" \
  -d '{"model":"openai/gpt-4o-mini","messages":[{"role":"user","content":"Hi"}]}'
```

If returns 200: Key works. Check .env formatting.
If returns 401: Key invalid. Get new key from dashboard.

### Problem: Rate limit errors occurring rapidly

**Solutions:**
- Gemini: Hit free tier quota (100k tokens/month). Switch to OpenRouter or wait for monthly reset.
- OpenRouter: Hit spend limit. Increase limit in dashboard or reduce evaluation frequency.
- Both: Evaluate same candidate instead of duplicates (implement caching TODO).

---

## Next Steps

### Immediate (Already Done)
- ✅ Smart inference module with fallback chain
- ✅ AI views updated to use smart inference
- ✅ Dual-provider support (Gemini + OpenRouter)

### Short-term (Recommended)
1. Get OpenRouter API key (https://openrouter.ai/)
2. Add to `.env`: `OPENROUTER_API_KEY=sk-or-v1-...` and `OPENROUTER_ENABLED=True`
3. Restart server and test `/api/v1/ai/status` endpoint
4. Test evaluation on a parsed resume to confirm fallback works

### Medium-term (Performance)
- [ ] Implement response caching (same reference_no + job role = cached 24h)
- [ ] Add Redis backend for distributed caching
- [ ] Monitor provider usage via dashboard
- [ ] Implement cost tracking and alerts

### Long-term (Scalability)
- [ ] Add third provider (Anthropic direct API)
- [ ] Implement adaptive model selection (cost vs quality)
- [ ] Build evaluation history and trends
- [ ] Add A/B testing between providers

---

## Quick Reference

### Environment Variables
```bash
# Gemini (Primary)
GEMINI_API_KEY=AIzaSyA...
GEMINI_ENABLED=True

# OpenRouter (Fallback)
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_ENABLED=True
OPENROUTER_MODEL=openai/gpt-4o-mini
```

### Main Entry Points
```python
from core.smart_inference import (
    smart_evaluate_candidate,      # POST /api/v1/candidates/{ref}/ai-evaluation
    smart_analyze_resume,          # GET /api/v1/candidates/{ref}/ai-analysis
    smart_generate_recommendations # POST /api/v1/candidates/{ref}/career-recommendations
)

from core.gemini_integration import is_gemini_enabled
from core.openrouter_integration import is_openrouter_enabled
```

### Status Endpoint
```
GET /api/v1/ai/status
→ Returns: available_providers, fallback_enabled, message
```

---

## Support

For issues:
1. Check `.env` configuration (newline at end, no trailing spaces)
2. Verify API keys are valid (test with curl)
3. Check rate limits (status endpoint shows provider status)
4. Review logs: `tail -f /tmp/django.log`

For OpenRouter support: https://openrouter.ai/docs/
For Gemini support: https://ai.google.dev/support/
