"""
OpenRouter AI Integration for Candidate Evaluation and Resume Analysis.
Provides fallback when Gemini is rate-limited or unavailable.
"""

import json
import os
from typing import Any

from django.conf import settings

try:
    import requests
except ImportError:
    requests = None


def _setting_value(name: str, default: Any = '') -> Any:
    return getattr(settings, name, os.getenv(name, default))


def _setting_bool(name: str, default: bool = False) -> bool:
    value = getattr(settings, name, os.getenv(name, str(default)))
    if isinstance(value, bool):
        return value
    return str(value).lower() in ('true', '1', 'yes')


def is_openrouter_enabled() -> bool:
    """Check if OpenRouter API is configured and enabled."""
    return _setting_bool('OPENROUTER_ENABLED', False) and bool(_setting_value('OPENROUTER_API_KEY', '')) and requests is not None


def evaluate_candidate_fit(
    reference_no: str,
    extracted_skills: list[str],
    roles: list[str],
    job_description: str,
    required_skills: list[str],
) -> dict[str, Any]:
    """
    Use OpenRouter AI to evaluate candidate fit for a job role.
    """
    if not is_openrouter_enabled():
        return {
            'status': 'disabled',
            'message': 'OpenRouter AI is not enabled. Configure OPENROUTER_API_KEY and set OPENROUTER_ENABLED=True.',
        }

    try:
        prompt = f"""
You are an expert recruitment analyst evaluating a candidate for a software engineering role.

Candidate Reference: {reference_no}

Extracted Skills: {', '.join(extracted_skills)}
Candidate Roles/Experience: {', '.join(roles)}

Job Role Requirements:
{job_description}

Required Skills for Role: {', '.join(required_skills)}

Please provide a JSON response with:
1. fit_score (0-100)
2. strengths (list of 2-3 strengths)
3. gaps (list of 2-3 skill gaps)
4. recommendations (list of 2-3 recommendations)
5. confidence (high/medium/low)
6. reasoning (brief explanation)

Format ONLY as valid JSON, no additional text.
"""

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {_setting_value('OPENROUTER_API_KEY', '')}",
                "HTTP-Referer": "https://gethired.local",
                "X-OpenRouter-Title": "GetHired Candidate Evaluation",
            },
            json={
                "model": _setting_value('OPENROUTER_MODEL', 'openai/gpt-4o-mini'),
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
            },
            timeout=30,
        )

        if response.status_code != 200:
            return {
                'status': 'error',
                'reference_no': reference_no,
                'error': f"HTTP {response.status_code}: {response.text}",
            }

        result = response.json()
        if 'choices' not in result or not result['choices']:
            return {
                'status': 'error',
                'reference_no': reference_no,
                'error': 'Invalid response from OpenRouter',
            }

        content = result['choices'][0]['message']['content']
        try:
            evaluation = json.loads(content)
            return {
                'status': 'success',
                'reference_no': reference_no,
                'ai_evaluation': evaluation,
                'model': _setting_value('OPENROUTER_MODEL', 'openai/gpt-4o-mini'),
                'provider': 'openrouter',
            }
        except json.JSONDecodeError:
            return {
                'status': 'success',
                'reference_no': reference_no,
                'ai_evaluation': {'raw_response': content},
                'model': _setting_value('OPENROUTER_MODEL', 'openai/gpt-4o-mini'),
                'provider': 'openrouter',
            }

    except requests.exceptions.Timeout:
        return {
            'status': 'error',
            'reference_no': reference_no,
            'error': 'OpenRouter request timed out',
        }
    except Exception as e:
        return {
            'status': 'error',
            'reference_no': reference_no,
            'error': str(e),
        }


def analyze_resume(
    reference_no: str,
    extracted_text: str,
    parsed_profile: dict[str, Any],
) -> dict[str, Any]:
    """
    Use OpenRouter AI for deep-dive resume analysis.
    """
    if not is_openrouter_enabled():
        return {'status': 'disabled', 'message': 'OpenRouter AI is not enabled.'}

    try:
        context = f"""
Candidate Reference: {reference_no}

Extracted Profile:
- Skills: {', '.join(parsed_profile.get('skills', [])[:10])}
- Roles: {', '.join(parsed_profile.get('roles', [])[:5])}
- Years of Experience: {parsed_profile.get('years_experience', 'Not found')}
- Education: {json.dumps(parsed_profile.get('education', [])[:2], indent=2)}
- Projects: {'; '.join([p[:100] for p in parsed_profile.get('projects', [])[:3]])}

Resume Excerpt (truncated):
{extracted_text[:1500]}

Analyze this resume and return ONLY a JSON array of job roles that fit the candidate.

Rules:
- Output only valid JSON.
- Return only role names.
- Do not include commentary, markdown, code fences, or explanation.
- Prefer roles supported by the resume evidence.

Format exactly as a JSON array, for example: ["Software Engineer", "Full Stack Developer"]
"""

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {_setting_value('OPENROUTER_API_KEY', '')}",
                "HTTP-Referer": "https://gethired.local",
                "X-OpenRouter-Title": "GetHired Resume Analysis",
            },
            json={
                "model": _setting_value('OPENROUTER_MODEL', 'openai/gpt-4o-mini'),
                "messages": [{"role": "user", "content": context}],
                "temperature": 0.7,
            },
            timeout=30,
        )

        if response.status_code != 200:
            return {
                'status': 'error',
                'reference_no': reference_no,
                'error': f"HTTP {response.status_code}",
            }

        result = response.json()
        if 'choices' not in result or not result['choices']:
            return {
                'status': 'error',
                'reference_no': reference_no,
                'error': 'Invalid response',
            }

        content = result['choices'][0]['message']['content']
        try:
            cleaned = content.strip()
            if cleaned.startswith('```'):
                cleaned = cleaned.strip('`').strip()
                if cleaned.lower().startswith('json'):
                    cleaned = cleaned[4:].strip()
            analysis = json.loads(cleaned)
            if not isinstance(analysis, list):
                analysis = analysis.get('job_roles', []) if isinstance(analysis, dict) else []
            return {
                'status': 'success',
                'reference_no': reference_no,
                'ai_analysis': {'job_roles': analysis},
                'model': _setting_value('OPENROUTER_MODEL', 'openai/gpt-4o-mini'),
                'provider': 'openrouter',
            }
        except json.JSONDecodeError:
            return {
                'status': 'success',
                'reference_no': reference_no,
                'ai_analysis': {'job_roles': parsed_profile.get('roles', [])},
                'model': _setting_value('OPENROUTER_MODEL', 'openai/gpt-4o-mini'),
                'provider': 'openrouter',
            }

    except Exception as e:
        return {
            'status': 'error',
            'reference_no': reference_no,
            'error': str(e),
        }


def generate_personalized_recommendations(
    reference_no: str,
    parsed_profile: dict[str, Any],
    target_roles: list[str],
) -> dict[str, Any]:
    """
    Use OpenRouter to generate career recommendations.
    """
    if not is_openrouter_enabled():
        return {'status': 'disabled', 'message': 'OpenRouter AI is not enabled.'}

    try:
        prompt = f"""
Career Development Advisor for Software Engineers

Candidate: {reference_no}
Current Skills: {', '.join(parsed_profile.get('skills', []))}
Current Roles: {', '.join(parsed_profile.get('roles', []))}
Experience: {parsed_profile.get('years_experience', '0')} years

Target Roles: {', '.join(target_roles)}

Create a career development plan as JSON with:
1. skill_roadmap (3-6 month priorities as dict)
2. certifications (list)
3. projects (list of project ideas)
4. community (list of engagement suggestions)
5. timeline (estimated months to reach target)

Format ONLY as valid JSON.
"""

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {_setting_value('OPENROUTER_API_KEY', '')}",
                "HTTP-Referer": "https://gethired.local",
                "X-OpenRouter-Title": "GetHired Career Recommendations",
            },
            json={
                "model": _setting_value('OPENROUTER_MODEL', 'openai/gpt-4o-mini'),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
            },
            timeout=30,
        )

        if response.status_code != 200:
            return {
                'status': 'error',
                'reference_no': reference_no,
                'error': f"HTTP {response.status_code}",
            }

        result = response.json()
        if 'choices' not in result or not result['choices']:
            return {
                'status': 'error',
                'reference_no': reference_no,
                'error': 'Invalid response',
            }

        content = result['choices'][0]['message']['content']
        try:
            recommendations = json.loads(content)
            return {
                'status': 'success',
                'reference_no': reference_no,
                'recommendations': recommendations,
                'target_roles': target_roles,
                'model': _setting_value('OPENROUTER_MODEL', 'openai/gpt-4o-mini'),
                'provider': 'openrouter',
            }
        except json.JSONDecodeError:
            return {
                'status': 'success',
                'reference_no': reference_no,
                'recommendations': {'raw_response': content},
                'target_roles': target_roles,
                'model': _setting_value('OPENROUTER_MODEL', 'openai/gpt-4o-mini'),
                'provider': 'openrouter',
            }

    except Exception as e:
        return {
            'status': 'error',
            'reference_no': reference_no,
            'error': str(e),
        }
