"""
Smart AI Inference with Fallback Strategy.
Routes between Gemini, OpenRouter, and rule-based evaluation based on availability and errors.
"""

import json
from typing import Any

from core.gemini_integration import (
    is_gemini_enabled,
    evaluate_candidate_fit as gemini_evaluate,
    analyze_resume as gemini_analyze,
    generate_personalized_recommendations as gemini_recommend,
)
from core.openrouter_integration import (
    is_openrouter_enabled,
    evaluate_candidate_fit as openrouter_evaluate,
    analyze_resume as openrouter_analyze,
    generate_personalized_recommendations as openrouter_recommend,
)


ROLE_REQUIREMENTS = {
    'software engineer': ['Python', 'SQL', 'Git', 'REST'],
    'backend engineer': ['Python', 'Django', 'REST', 'SQL', 'Docker'],
    'backend developer': ['Python', 'Django', 'REST', 'SQL', 'Docker'],
    'full stack developer': ['React', 'Node.js', 'SQL', 'REST', 'Git'],
    'full-stack developer': ['React', 'Node.js', 'SQL', 'REST', 'Git'],
    'devops engineer': ['Docker', 'Kubernetes', 'Linux', 'CI/CD', 'AWS', 'Azure'],
    'cloud engineer': ['AWS', 'Azure', 'Docker', 'Kubernetes', 'Linux'],
    'data engineer': ['Python', 'SQL', 'Pandas', 'NumPy'],
    'machine learning engineer': ['Python', 'Machine Learning', 'TensorFlow', 'Pandas', 'NumPy'],
}


def _rule_based_evaluation(
    reference_no: str,
    extracted_skills: list[str],
    roles: list[str],
    required_skills: list[str],
) -> dict[str, Any]:
    """
    Fallback rule-based evaluation when AI providers are unavailable.
    Pure skill matching without AI inference.
    """
    matched = [skill for skill in required_skills if skill in extracted_skills]
    missing = [skill for skill in required_skills if skill not in extracted_skills]

    fit_score = 0
    if required_skills:
        fit_score = round(100 * len(matched) / len(required_skills))
    
    strengths = [
        f"Has {skill} experience" for skill in matched[:3]
    ] or ["Demonstrates willingness to learn"]
    
    gaps = [
        f"Missing: {skill}" for skill in missing[:3]
    ] or ["All required skills present"]

    recommendations = [
        f"Strengthen {skill} expertise" for skill in missing[:2]
    ] or [
        "Strong candidate profile",
        "Consider specialized projects to deepen expertise",
    ]

    return {
        'fit_score': fit_score,
        'strengths': strengths,
        'gaps': gaps,
        'recommendations': recommendations,
        'confidence': 'high' if fit_score >= 80 else 'medium' if fit_score >= 50 else 'low',
        'reasoning': f"Rule-based evaluation: {len(matched)}/{len(required_skills)} skills matched",
    }


def smart_evaluate_candidate(
    reference_no: str,
    extracted_skills: list[str],
    roles: list[str],
    job_description: str,
    required_skills: list[str],
) -> dict[str, Any]:
    """
    Smart AI inference with fallback chain:
    1. Try Gemini (preferred)
    2. If rate-limited, try OpenRouter
    3. If both fail, use rule-based evaluation
    """
    evaluation = None
    provider = None
    fallback_reason = None

    # Try Gemini first
    if is_gemini_enabled():
        result = gemini_evaluate(
            reference_no=reference_no,
            extracted_skills=extracted_skills,
            roles=roles,
            job_description=job_description,
            required_skills=required_skills,
        )
        if result.get('status') == 'success':
            return {
                **result,
                'fallback_used': False,
                'provider': 'gemini',
            }
        fallback_reason = result.get('error', 'Gemini unavailable')

    # Try OpenRouter as fallback
    if is_openrouter_enabled():
        result = openrouter_evaluate(
            reference_no=reference_no,
            extracted_skills=extracted_skills,
            roles=roles,
            job_description=job_description,
            required_skills=required_skills,
        )
        if result.get('status') == 'success':
            return {
                **result,
                'fallback_used': True,
                'fallback_reason': fallback_reason,
                'provider': 'openrouter',
            }

    # Fall back to rule-based evaluation
    rule_based = _rule_based_evaluation(
        reference_no=reference_no,
        extracted_skills=extracted_skills,
        roles=roles,
        required_skills=required_skills,
    )

    return {
        'status': 'success',
        'reference_no': reference_no,
        'ai_evaluation': rule_based,
        'model': 'rule-based',
        'provider': 'fallback',
        'fallback_used': True,
        'fallback_reason': 'All AI providers unavailable; using rule-based matching',
    }


def smart_analyze_resume(
    reference_no: str,
    extracted_text: str,
    parsed_profile: dict[str, Any],
) -> dict[str, Any]:
    """
    Smart resume analysis with provider fallback chain.
    Returns only job roles extracted or inferred from the resume.
    """
    # Try Gemini
    if is_gemini_enabled():
        result = gemini_analyze(
            reference_no=reference_no,
            extracted_text=extracted_text,
            parsed_profile=parsed_profile,
        )
        if result.get('status') == 'success':
            return {**result, 'fallback_used': False}

    # Try OpenRouter
    if is_openrouter_enabled():
        result = openrouter_analyze(
            reference_no=reference_no,
            extracted_text=extracted_text,
            parsed_profile=parsed_profile,
        )
        if result.get('status') == 'success':
            return {**result, 'fallback_used': True}

    return {
        'status': 'success',
        'reference_no': reference_no,
        'ai_analysis': {
            'job_roles': parsed_profile.get('roles', []),
        },
        'model': 'rule-based',
        'provider': 'fallback',
        'fallback_used': True,
    }


def smart_generate_recommendations(
    reference_no: str,
    parsed_profile: dict[str, Any],
    target_roles: list[str],
) -> dict[str, Any]:
    """
    Smart recommendations with provider fallback chain.
    """
    # Try Gemini
    if is_gemini_enabled():
        result = gemini_recommend(
            reference_no=reference_no,
            parsed_profile=parsed_profile,
            target_roles=target_roles,
        )
        if result.get('status') == 'success':
            return {**result, 'fallback_used': False}

    # Try OpenRouter
    if is_openrouter_enabled():
        result = openrouter_recommend(
            reference_no=reference_no,
            parsed_profile=parsed_profile,
            target_roles=target_roles,
        )
        if result.get('status') == 'success':
            return {**result, 'fallback_used': True}

    # Fallback to generic recommendations
    skills = parsed_profile.get('skills', [])
    missing_skills = [
        skill for skill in ['Docker', 'Kubernetes', 'AWS', 'System Design']
        if skill not in skills
    ]

    return {
        'status': 'success',
        'reference_no': reference_no,
        'recommendations': {
            'skill_roadmap': {
                'month_1_2': missing_skills[:2],
                'month_3_4': ['Advanced system design', 'Open source contribution'],
                'month_5_6': ['Lead a production project', 'Mentor junior developers'],
            },
            'certifications': [
                'AWS Solutions Architect Associate',
                'Certified Kubernetes Administrator',
            ],
            'projects': [
                'Build and deploy a production-grade microservice',
                'Implement CI/CD pipeline for existing project',
                'Contribute to major open-source project',
            ],
            'community': [
                'Join technology-specific meetup groups',
                'Write technical blog posts',
                'Speak at local tech conferences',
            ],
            'timeline': '6-9 months to reach target role',
        },
        'target_roles': target_roles,
        'model': 'rule-based',
        'provider': 'fallback',
        'fallback_used': True,
    }
