"""
AI-powered evaluation endpoints with smart fallback system.
Routes between Gemini, OpenRouter, and rule-based evaluation.
"""

import hashlib
import json

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ingestion.models import ResumeUploadRecord
from core.gemini_integration import is_gemini_enabled
from core.openrouter_integration import is_openrouter_enabled
from core.smart_inference import (
    smart_evaluate_candidate,
    smart_analyze_resume,
    smart_generate_recommendations,
)


def _stable_hash(value) -> str:
    normalized = json.dumps(value, sort_keys=True, separators=(',', ':'), default=str)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def _profile_fingerprint(record: ResumeUploadRecord) -> str:
    parsed_json = record.parsed_json if isinstance(record.parsed_json, dict) else {}
    payload = {
        'structured_profile': parsed_json.get('structured_profile', {}),
        'storage_backend': record.storage_backend,
        'storage_key': record.storage_key,
        'object_etag': record.object_etag,
        'object_size': record.object_size,
        'parsed_at': record.parsed_at.isoformat() if record.parsed_at else None,
        'status': record.status,
    }
    return _stable_hash(payload)


def _cache_key(prefix: str, signature: dict | None = None) -> str:
    if not signature:
        return prefix
    return f"{prefix}::{_stable_hash(signature)}"


def _get_cached_result(record: ResumeUploadRecord, key: str, fingerprint: str) -> dict | None:
    parsed_json = record.parsed_json if isinstance(record.parsed_json, dict) else {}
    ai_cache = parsed_json.get('ai_cache', {}) if isinstance(parsed_json.get('ai_cache', {}), dict) else {}
    entry = ai_cache.get(key)
    if not isinstance(entry, dict):
        return None
    if entry.get('fingerprint') != fingerprint:
        return None
    result = entry.get('result')
    if not isinstance(result, dict):
        return None

    cached = dict(result)
    cached['cache_hit'] = True
    cached['cached_at'] = entry.get('updated_at')
    return cached


def _set_cached_result(record: ResumeUploadRecord, key: str, fingerprint: str, result: dict) -> None:
    parsed_json = dict(record.parsed_json or {})
    ai_cache = parsed_json.get('ai_cache', {})
    if not isinstance(ai_cache, dict):
        ai_cache = {}

    ai_cache[key] = {
        'fingerprint': fingerprint,
        'result': result,
        'updated_at': timezone.now().isoformat(),
    }

    parsed_json['ai_cache'] = ai_cache
    record.parsed_json = parsed_json
    record.save(update_fields=['parsed_json', 'updated_at'])


class GeminiStatusView(APIView):
    """Check if AI providers are enabled and ready."""
    permission_classes = [AllowAny]

    def get(self, request):
        gemini_ok = is_gemini_enabled()
        openrouter_ok = is_openrouter_enabled()
        providers = []
        if gemini_ok:
            providers.append('gemini')
        if openrouter_ok:
            providers.append('openrouter')
        
        available = 'Multiple providers available' if len(providers) > 1 else (
            f'{providers[0]} ready' if providers else 'No AI providers configured'
        )
        
        return Response(
            {
                'gemini_enabled': gemini_ok,
                'openrouter_enabled': openrouter_ok,
                'available_providers': providers,
                'status': 'ready' if providers else 'not_configured',
                'message': available,
                'fallback_enabled': len(providers) > 1,
            },
            status=status.HTTP_200_OK,
        )


class CandidateAIEvaluationView(APIView):
    """AI-powered candidate evaluation for a specific job role."""
    permission_classes = [AllowAny]

    def post(self, request, reference_no: str):
        if not is_gemini_enabled() and not is_openrouter_enabled():
            return Response(
                {
                    'detail': 'No AI providers configured.',
                    'message': 'Set GEMINI_API_KEY or OPENROUTER_API_KEY in .env with provider enabled.',
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        record = ResumeUploadRecord.objects.filter(reference_no=reference_no).first()
        if not record or not record.parsed_json:
            return Response(
                {
                    'detail': 'Resume not found or not yet parsed.',
                    'reference_no': reference_no,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        parsed_profile = record.parsed_json.get('structured_profile', {})
        extracted_skills = parsed_profile.get('skills', [])
        roles = parsed_profile.get('roles', [])

        job_description = str(request.data.get('job_description', '')).strip()
        required_skills = request.data.get('required_skills', [])
        if not required_skills:
            required_skills = extracted_skills[:5]

        if not job_description:
            job_description = f"Candidate for roles: {', '.join(roles)}"

        fingerprint = _profile_fingerprint(record)
        key = _cache_key(
            'evaluation',
            {
                'job_description': job_description,
                'required_skills': sorted(str(skill) for skill in required_skills),
            },
        )
        cached = _get_cached_result(record, key, fingerprint)
        if cached:
            return Response(cached, status=status.HTTP_200_OK)

        result = smart_evaluate_candidate(
            reference_no=reference_no,
            extracted_skills=extracted_skills,
            roles=roles,
            job_description=job_description,
            required_skills=required_skills,
        )

        if result.get('status') == 'success':
            _set_cached_result(record, key, fingerprint, result)
            result = {**result, 'cache_hit': False}

        return Response(result, status=status.HTTP_200_OK)


class ResumeAIAnalysisView(APIView):
    """Deep-dive AI analysis of resume and candidate profile."""
    permission_classes = [AllowAny]

    def get(self, request, reference_no: str):
        if not is_gemini_enabled() and not is_openrouter_enabled():
            return Response(
                {
                    'detail': 'No AI providers configured.',
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        record = ResumeUploadRecord.objects.filter(reference_no=reference_no).first()
        if not record or not record.parsed_json:
            return Response(
                {
                    'detail': 'Resume not found or not yet parsed.',
                    'reference_no': reference_no,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        extracted_text = request.data.get('extracted_text', '') if hasattr(request, 'data') and request.data else ''
        if not extracted_text:
            try:
                from ingestion.storage import read_resume_file
                content = read_resume_file(record.storage_backend, record.storage_key)
                from ingestion.views import _extract_text
                extracted_text = _extract_text(content)
            except Exception:
                extracted_text = ''

        parsed_profile = record.parsed_json.get('structured_profile', {})

        fingerprint = _profile_fingerprint(record)
        key = _cache_key(
            'analysis',
            {
                'custom_text_hash': _stable_hash(extracted_text) if extracted_text else '',
            },
        )
        cached = _get_cached_result(record, key, fingerprint)
        if cached:
            return Response(cached, status=status.HTTP_200_OK)

        result = smart_analyze_resume(
            reference_no=reference_no,
            extracted_text=extracted_text,
            parsed_profile=parsed_profile,
        )

        if result.get('status') == 'success':
            _set_cached_result(record, key, fingerprint, result)
            result = {**result, 'cache_hit': False}

        return Response(result, status=status.HTTP_200_OK)


class CareerRecommendationsView(APIView):
    """AI-generated personalized career development recommendations."""
    permission_classes = [AllowAny]

    def post(self, request, reference_no: str):
        if not is_gemini_enabled() and not is_openrouter_enabled():
            return Response(
                {
                    'detail': 'No AI providers configured.',
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        record = ResumeUploadRecord.objects.filter(reference_no=reference_no).first()
        if not record or not record.parsed_json:
            return Response(
                {
                    'detail': 'Resume not found or not yet parsed.',
                    'reference_no': reference_no,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        parsed_profile = record.parsed_json.get('structured_profile', {})
        target_roles = request.data.get('target_roles', [])
        if not target_roles:
            target_roles = parsed_profile.get('roles', ['Software Engineer'])[:3]

        fingerprint = _profile_fingerprint(record)
        key = _cache_key(
            'recommendations',
            {
                'target_roles': sorted(str(role) for role in target_roles),
            },
        )
        cached = _get_cached_result(record, key, fingerprint)
        if cached:
            return Response(cached, status=status.HTTP_200_OK)

        result = smart_generate_recommendations(
            reference_no=reference_no,
            parsed_profile=parsed_profile,
            target_roles=target_roles,
        )

        if result.get('status') == 'success':
            _set_cached_result(record, key, fingerprint, result)
            result = {**result, 'cache_hit': False}

        return Response(result, status=status.HTTP_200_OK)
