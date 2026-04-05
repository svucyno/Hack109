from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


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
    permission_classes = [AllowAny]

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
