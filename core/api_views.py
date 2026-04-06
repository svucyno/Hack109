from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from ingestion.models import ResumeUploadRecord


class HrOverviewView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                'role': 'hr',
                'title': 'HR Talent Dashboard',
                'description': 'Blind-evaluation view with resume ingestion entry point.',
                'candidate_refs': ['REF-001', 'REF-002', 'REF-003'],
                'actions': {
                    'score_endpoint': '/api/v1/candidates/{reference_no}/score',
                    'resume_upload_endpoint': '/api/v1/resumes/upload-url',
                    'resume_register_endpoint': '/api/v1/resumes/register-upload',
                },
            }
        )


class StudentOverviewView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                'role': 'student',
                'title': 'Student Career Page',
                'description': 'Role recommendations, skill gaps, and course guidance.',
                'actions': {
                    'recommendations_endpoint': '/api/v1/students/{user_id}/recommendations',
                },
                'default_user': 'student-demo-001',
            }
        )


class AdminOverviewView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response(
            {
                'role': 'admin',
                'title': 'Admin Governance Page',
                'description': 'Audit coverage, fairness checks, and policy controls.',
                'metrics': {
                    'deanonymize_audit_target': '100%',
                    'fairness_dir_threshold': '0.80',
                },
                'actions': {
                    'privacy_redact_endpoint': '/api/v1/privacy/redact',
                    'privacy_validate_endpoint': '/api/v1/privacy/validate',
                    'privacy_report_endpoint': '/api/v1/privacy/{reference_no}/report',
                },
            }
        )


class AdminResumeRecordsView(APIView):
    """Admin-only overview of all parsed resumes and cached AI artifacts."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        records = ResumeUploadRecord.objects.order_by('-updated_at')
        items = []
        for record in records:
            parsed_json = record.parsed_json if isinstance(record.parsed_json, dict) else {}
            structured = parsed_json.get('structured_profile', {}) if isinstance(parsed_json.get('structured_profile', {}), dict) else {}
            ai_cache = parsed_json.get('ai_cache', {}) if isinstance(parsed_json.get('ai_cache', {}), dict) else {}
            items.append(
                {
                    'reference_no': record.reference_no,
                    'status': record.status,
                    'original_filename': record.original_filename,
                    'content_type': record.content_type,
                    'storage_backend': record.storage_backend,
                    'storage_key': record.storage_key,
                    'object_size': record.object_size,
                    'object_etag': record.object_etag,
                    'parsed_at': record.parsed_at,
                    'created_at': record.created_at,
                    'updated_at': record.updated_at,
                    'skills': structured.get('skills', []),
                    'roles': structured.get('roles', []),
                    'years_experience': structured.get('years_experience'),
                    'ai_cache_keys': list(ai_cache.keys()),
                }
            )

        return Response(
            {
                'count': len(items),
                'results': items,
            }
        )


class AdminResumeRecordDetailView(APIView):
    """Admin-only full detail for a specific reference including parsed JSONB and AI cache."""

    permission_classes = [IsAdminUser]

    def get(self, request, reference_no: str):
        record = ResumeUploadRecord.objects.filter(reference_no=reference_no).first()
        if not record:
            return Response({'detail': 'Reference not found.', 'reference_no': reference_no}, status=404)

        parsed_json = record.parsed_json if isinstance(record.parsed_json, dict) else {}

        return Response(
            {
                'reference_no': record.reference_no,
                'status': record.status,
                'original_filename': record.original_filename,
                'content_type': record.content_type,
                'storage_backend': record.storage_backend,
                'storage_key': record.storage_key,
                'object_size': record.object_size,
                'object_etag': record.object_etag,
                'parsed_at': record.parsed_at,
                'created_at': record.created_at,
                'updated_at': record.updated_at,
                'parsed_json': parsed_json,
            }
        )
