"""
AI-powered evaluation endpoints with smart fallback system.
Routes between Gemini, OpenRouter, and rule-based evaluation.
"""

import hashlib
import json
from datetime import datetime, timedelta

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


def _parse_csv_list(raw_value) -> list[str]:
    if isinstance(raw_value, list):
        return [str(item).strip() for item in raw_value if str(item).strip()]
    if not raw_value:
        return []
    return [part.strip() for part in str(raw_value).split(',') if part.strip()]


LINK_VERIFICATION_TTL_HOURS = 24


def _parse_verified_at(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if timezone.is_naive(parsed):
            parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
        return parsed
    except Exception:
        return None


def _refresh_verified_links_if_needed(record: ResumeUploadRecord, parsed_profile: dict) -> dict:
    links = [str(item).strip() for item in (parsed_profile.get('links') or []) if str(item).strip()]
    verified_links = [item for item in (parsed_profile.get('verified_links') or []) if isinstance(item, dict)]

    if not links:
        return parsed_profile

    now = timezone.now()
    has_stale_entries = any(
        (
            (verified_at := _parse_verified_at(str(entry.get('verified_at', '')))) is None
            or (now - verified_at) > timedelta(hours=LINK_VERIFICATION_TTL_HOURS)
        )
        for entry in verified_links
    )
    needs_refresh = (not verified_links) or has_stale_entries
    if not needs_refresh:
        return parsed_profile

    from ingestion.views import _verify_links

    refreshed = _verify_links(links)

    parsed_json = dict(record.parsed_json or {})
    structured_profile = dict(parsed_json.get('structured_profile') or {})
    parse_meta = dict(parsed_json.get('parse_meta') or {})

    structured_profile['links'] = links
    structured_profile['verified_links'] = refreshed
    parse_meta['verified_links_count'] = len(refreshed)

    parsed_json['structured_profile'] = structured_profile
    parsed_json['parse_meta'] = parse_meta
    record.parsed_json = parsed_json
    record.save(update_fields=['parsed_json', 'updated_at'])

    return structured_profile


def _build_link_evidence(parsed_profile: dict) -> dict:
    links = [str(item).strip() for item in (parsed_profile.get('links') or []) if str(item).strip()]
    verified_links = [item for item in (parsed_profile.get('verified_links') or []) if isinstance(item, dict)]

    reachable = [item for item in verified_links if bool(item.get('reachable'))]
    unreachable = [item for item in verified_links if not bool(item.get('reachable'))]
    github_profiles = [item for item in reachable if item.get('type') == 'github_profile']
    github_repositories = [item for item in reachable if item.get('type') == 'github_repository']
    production_links = [item for item in reachable if item.get('type') == 'production_link']

    return {
        'total_links': len(links),
        'verified_total': len(verified_links),
        'reachable_total': len(reachable),
        'unreachable_total': len(unreachable),
        'github_profiles': len(github_profiles),
        'github_repositories': len(github_repositories),
        'production_links': len(production_links),
        'reachable_urls': [str(item.get('url', '')) for item in reachable[:8]],
    }


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
        parsed_profile = _refresh_verified_links_if_needed(record, parsed_profile)
        link_evidence = _build_link_evidence(parsed_profile)
        extracted_skills = parsed_profile.get('skills', [])
        roles = parsed_profile.get('roles', [])

        role_name = str(request.data.get('role_name', '')).strip()
        experience_required = request.data.get('required_experience_years')
        try:
            required_experience_years = int(experience_required) if experience_required is not None else None
        except (TypeError, ValueError):
            required_experience_years = None

        must_have_skills = _parse_csv_list(request.data.get('must_have_skills'))
        nice_to_have_skills = _parse_csv_list(request.data.get('nice_to_have_skills'))
        tech_stack = _parse_csv_list(request.data.get('tech_stack'))
        additional_parameters = str(request.data.get('other_parameters', '')).strip()

        required_skills = _parse_csv_list(request.data.get('required_skills'))
        if not required_skills:
            required_skills = list(dict.fromkeys(must_have_skills + tech_stack))
        if not required_skills:
            required_skills = extracted_skills[:5]

        min_fit_score = request.data.get('min_fit_score', 70)
        try:
            min_fit_score = int(min_fit_score)
        except (TypeError, ValueError):
            min_fit_score = 70

        job_description = str(request.data.get('job_description', '')).strip()
        if not job_description:
            fragments = [
                f"Role: {role_name or 'General Software Role'}",
                f"Must-have skills: {', '.join(must_have_skills) if must_have_skills else 'Not specified'}",
                f"Tech stack: {', '.join(tech_stack) if tech_stack else 'Not specified'}",
                f"Nice-to-have skills: {', '.join(nice_to_have_skills) if nice_to_have_skills else 'Not specified'}",
                f"Required experience (years): {required_experience_years if required_experience_years is not None else 'Not specified'}",
                f"Other parameters: {additional_parameters or 'Not specified'}",
            ]
            job_description = '\n'.join(fragments)

        fingerprint = _profile_fingerprint(record)
        key = _cache_key(
            'evaluation',
            {
                'job_description': job_description,
                'required_skills': sorted(str(skill) for skill in required_skills),
                'role_name': role_name,
                'required_experience_years': required_experience_years,
                'must_have_skills': sorted(must_have_skills),
                'nice_to_have_skills': sorted(nice_to_have_skills),
                'tech_stack': sorted(tech_stack),
                'other_parameters': additional_parameters,
                'min_fit_score': min_fit_score,
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
            link_evidence=link_evidence,
        )

        if result.get('status') == 'success':
            fit_score = (((result.get('ai_evaluation') or {}).get('fit_score')) if isinstance(result.get('ai_evaluation'), dict) else None)
            try:
                fit_score = int(fit_score)
            except (TypeError, ValueError):
                fit_score = 0

            pass_decision = fit_score >= min_fit_score
            profile_years = parsed_profile.get('years_experience')
            experience_pass = True
            if required_experience_years is not None and isinstance(profile_years, int):
                experience_pass = profile_years >= required_experience_years
            elif required_experience_years is not None and profile_years is None:
                experience_pass = False

            final_pass = pass_decision and experience_pass

            result = {
                **result,
                'evaluation_input': {
                    'role_name': role_name,
                    'must_have_skills': must_have_skills,
                    'nice_to_have_skills': nice_to_have_skills,
                    'tech_stack': tech_stack,
                    'required_skills': required_skills,
                    'required_experience_years': required_experience_years,
                    'min_fit_score': min_fit_score,
                    'other_parameters': additional_parameters,
                },
                'resume_profile_snapshot': {
                    'skills': extracted_skills,
                    'roles': roles,
                    'years_experience': parsed_profile.get('years_experience'),
                    'links': parsed_profile.get('links', []),
                    'link_evidence': link_evidence,
                },
                'comparison': {
                    'fit_score': fit_score,
                    'fit_threshold_passed': pass_decision,
                    'experience_threshold_passed': experience_pass,
                    'decision': 'PASS' if final_pass else 'NOT_PASS',
                    'is_resume_suitable': final_pass,
                },
            }

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
