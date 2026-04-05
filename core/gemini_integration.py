"""
Google Gemini AI Integration for Candidate Evaluation and Resume Analysis.
Provides utilities for AI-powered job fit assessment and skill gap analysis.
"""

import json
import os
from typing import Any

from django.conf import settings

try:
    import google.genai as genai
    from google.genai.types import GenerateContentConfig
except ImportError:
    genai = None


GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_ENABLED = os.getenv('GEMINI_ENABLED', 'False').lower() in ('true', '1', 'yes')


def _gemini_model_name() -> str:
    return getattr(settings, 'GEMINI_MODEL', os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-lite'))


def _extract_json_payload(response_text: str) -> str:
    cleaned = response_text.strip()
    if cleaned.startswith('```'):
        cleaned = cleaned.strip('`').strip()
        if cleaned.lower().startswith('json'):
            cleaned = cleaned[4:].strip()

    json_start = cleaned.find('{')
    json_end = cleaned.rfind('}') + 1
    if json_start >= 0 and json_end > json_start:
        return cleaned[json_start:json_end]
    return cleaned


def is_gemini_enabled() -> bool:
    """Check if Gemini API is configured and enabled."""
    return GEMINI_ENABLED and GEMINI_API_KEY and genai is not None


def _get_gemini_client():
    """Get or initialize Gemini client."""
    if not is_gemini_enabled():
        return None
    try:
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception:
        return None


def evaluate_candidate_fit(
    reference_no: str,
    extracted_skills: list[str],
    roles: list[str],
    job_description: str,
    required_skills: list[str],
) -> dict[str, Any]:
    """
    Use Gemini AI to evaluate candidate fit for a job role.
    
    Args:
        reference_no: Resume reference ID.
        extracted_skills: List of skills extracted from resume.
        roles: Job titles/roles from resume.
        job_description: Job description or role requirements.
        required_skills: Key skills needed for the role.
    
    Returns:
        Dict with AI evaluation including fit_score, insights, and recommendations.
    """
    if not is_gemini_enabled():
        return {
            'status': 'disabled',
            'message': 'Gemini AI is not enabled. Configure GEMINI_API_KEY and set GEMINI_ENABLED=True.',
        }

    try:
        client = _get_gemini_client()
        if not client:
            return {'status': 'error', 'message': 'Failed to initialize Gemini client'}

        prompt = f"""
You are an expert recruitment analyst evaluating a candidate for a software engineering role.

Candidate Reference: {reference_no}

Extracted Skills: {', '.join(extracted_skills)}
Candidate Roles/Experience: {', '.join(roles)}

Job Role Requirements:
{job_description}

Required Skills for Role: {', '.join(required_skills)}

Please provide:
1. A fit score (0-100) based on skill alignment and role experience.
2. Key strengths of the candidate for this role.
3. Skill gaps that should be addressed.
4. Specific recommendations for the candidate to improve fit.
5. Confidence level (high, medium, low) in the evaluation.

Format your response as JSON with keys: fit_score, strengths, gaps, recommendations, confidence, reasoning.
"""

        response = client.models.generate_content(
            model=_gemini_model_name(),
            contents=prompt,
            config=GenerateContentConfig(temperature=0.7)
        )
        response_text = response.text

        try:
            payload = _extract_json_payload(response_text)
            evaluation = json.loads(payload)
            if isinstance(evaluation, list):
                evaluation = {'job_roles': evaluation}
            elif isinstance(evaluation, dict) and 'job_roles' not in evaluation:
                evaluation['job_roles'] = evaluation.get('roles', [])
            return {
                'status': 'success',
                'reference_no': reference_no,
                'ai_evaluation': evaluation,
                'model': _gemini_model_name(),
            }
        except json.JSONDecodeError:
            pass

        return {
            'status': 'success',
            'reference_no': reference_no,
            'ai_evaluation': {
                'raw_response': response_text,
                'reasoning': 'Could not parse structured JSON; raw AI response provided.',
            },
            'model': _gemini_model_name(),
        }

    except Exception as e:
        return {
            'status': 'error',
            'reference_no': reference_no,
            'error': str(e),
            'message': 'AI evaluation failed. Check API configuration and rate limits.',
        }


def analyze_resume(
    reference_no: str,
    extracted_text: str,
    parsed_profile: dict[str, Any],
) -> dict[str, Any]:
    """
    Use Gemini AI for deep-dive resume analysis beyond rule-based extraction.
    
    Args:
        reference_no: Resume reference ID.
        extracted_text: Raw text extracted from resume.
        parsed_profile: Parsed resume profile (skills, roles, education, etc.).
    
    Returns:
        Dict with AI insights including strengths, experiences, and development areas.
    """
    if not is_gemini_enabled():
        return {'status': 'disabled', 'message': 'Gemini AI is not enabled.'}

    try:
        client = _get_gemini_client()
        if not client:
            return {'status': 'error', 'message': 'Failed to initialize Gemini client'}

        context = f"""
Candidate Reference: {reference_no}

Extracted Profile:
- Skills: {', '.join(parsed_profile.get('skills', [])[:10])}
- Roles: {', '.join(parsed_profile.get('roles', [])[:5])}
- Years of Experience: {parsed_profile.get('years_experience', 'Not found')}
- Education: {json.dumps(parsed_profile.get('education', [])[:2], indent=2)}
- Projects: {'; '.join([p[:100] for p in parsed_profile.get('projects', [])[:3]])}

Resume Text Excerpt (truncated):
{extracted_text[:1500]}

Based on this resume, return ONLY a JSON array of job roles that fit the candidate.

Rules:
- Output only valid JSON.
- Return only role names.
- Do not include commentary, markdown, code fences, or explanation.
- Prefer roles supported by the resume evidence.

Format exactly as a JSON array, for example: ["Software Engineer", "Full Stack Developer"]
"""

        response = client.models.generate_content(
            model=_gemini_model_name(),
            contents=context,
            config=GenerateContentConfig(temperature=0.7)
        )
        response_text = response.text

        try:
            payload = _extract_json_payload(response_text)
            analysis = json.loads(payload)
            if not isinstance(analysis, list):
                analysis = analysis.get('job_roles', []) if isinstance(analysis, dict) else []
            return {
                'status': 'success',
                'reference_no': reference_no,
                'ai_analysis': {'job_roles': analysis},
                'model': _gemini_model_name(),
            }
        except json.JSONDecodeError:
            pass

        return {
            'status': 'success',
            'reference_no': reference_no,
            'ai_analysis': {'job_roles': parsed_profile.get('roles', [])},
            'model': _gemini_model_name(),
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
    Use Gemini to generate personalized learning and career recommendations.
    
    Args:
        reference_no: Resume reference ID.
        parsed_profile: Parsed resume profile.
        target_roles: Goal job roles for the candidate.
    
    Returns:
        Dict with recommendations including skill development paths and learning resources.
    """
    if not is_gemini_enabled():
        return {'status': 'disabled', 'message': 'Gemini AI is not enabled.'}

    try:
        client = _get_gemini_client()
        if not client:
            return {'status': 'error', 'message': 'Failed to initialize Gemini client'}

        prompt = f"""
You are a career development advisor for a software engineer.

Candidate Reference: {reference_no}
Current Skills: {', '.join(parsed_profile.get('skills', []))}
Current Roles/Experience: {', '.join(parsed_profile.get('roles', []))}
Years of Experience: {parsed_profile.get('years_experience', '0')}

Target Roles: {', '.join(target_roles)}

Based on this career profile, provide:
1. Skill development roadmap (3-6 month priorities).
2. Recommended certifications or learning paths.
3. Project portfolio recommendations.
4. Mentorship or community engagement suggestions.
5. Timeline estimate to reach target role level.

Format as JSON with keys: skill_roadmap, certifications, projects, community, timeline.
"""

        response = client.models.generate_content(
            model=_gemini_model_name(),
            contents=prompt,
            config=GenerateContentConfig(temperature=0.7)
        )
        response_text = response.text

        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                recommendations = json.loads(response_text[json_start:json_end])
                return {
                    'status': 'success',
                    'reference_no': reference_no,
                    'recommendations': recommendations,
                    'target_roles': target_roles,
                    'model': _gemini_model_name(),
                }
        except json.JSONDecodeError:
            pass

        return {
            'status': 'success',
            'reference_no': reference_no,
            'recommendations': {'raw_response': response_text},
            'model': _gemini_model_name(),
        }

    except Exception as e:
        return {
            'status': 'error',
            'reference_no': reference_no,
            'error': str(e),
        }
