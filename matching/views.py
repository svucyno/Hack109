from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ingestion.models import ResumeUploadRecord


CANDIDATE_SCORES = {
    'REF-001': {
        'reference_no': 'REF-001',
        'score_normalized': 0.91,
        'score_bucket': 5,
        'explanation': 'Strong overlap in distributed systems, Python backend APIs, and event-driven architecture.',
        'matched_skills': ['Python', 'Django', 'PostgreSQL', 'REST'],
        'missing_skills': ['Kubernetes'],
    },
    'REF-002': {
        'reference_no': 'REF-002',
        'score_normalized': 0.78,
        'score_bucket': 4,
        'explanation': 'Relevant API and data modeling experience with moderate gaps in observability tooling.',
        'matched_skills': ['Python', 'FastAPI', 'Redis'],
        'missing_skills': ['Prometheus', 'OpenTelemetry'],
    },
    'REF-003': {
        'reference_no': 'REF-003',
        'score_normalized': 0.63,
        'score_bucket': 3,
        'explanation': 'Good fundamentals and project depth, but skill coverage is partial for senior profile requirements.',
        'matched_skills': ['JavaScript', 'Node.js', 'SQL'],
        'missing_skills': ['Django', 'Vector Search'],
    },
}

STUDENT_RECOMMENDATIONS = {
    'student-demo-001': {
        'recommendations': [
            {'role_path': 'Backend Engineer', 'confidence': 0.88},
            {'role_path': 'ML Platform Associate', 'confidence': 0.73},
            {'role_path': 'Data Engineer', 'confidence': 0.67},
        ],
        'skill_gaps': ['System Design', 'Docker', 'Model Evaluation Basics'],
        'courses': [
            {
                'title': 'Scalable Backend Systems',
                'provider': 'Coursera',
                'duration': '5 weeks',
                'level': 'Intermediate',
                'url': 'https://www.coursera.org',
            },
            {
                'title': 'Cloud Native Foundations',
                'provider': 'NPTEL',
                'duration': '8 weeks',
                'level': 'Beginner',
                'url': 'https://nptel.ac.in',
            },
            {
                'title': 'ML Evaluation and Fairness',
                'provider': 'Coursera',
                'duration': '4 weeks',
                'level': 'Intermediate',
                'url': 'https://www.coursera.org',
            },
        ],
    },
}

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


def _normalize_role_input(role: str) -> str:
    lowered = role.lower().strip()
    if lowered in ROLE_REQUIREMENTS:
        return lowered
    for candidate in ROLE_REQUIREMENTS:
        if candidate in lowered or lowered in candidate:
            return candidate
    return lowered


class CandidateScoreView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, reference_no: str):
        role_input = str(request.query_params.get('role', '')).strip()

        record = ResumeUploadRecord.objects.filter(reference_no=reference_no).first()
        parsed_profile = None
        if record and isinstance(record.parsed_json, dict):
            parsed_profile = (record.parsed_json or {}).get('structured_profile') or {}

        if parsed_profile:
            extracted_skills = parsed_profile.get('skills') or []
            parsed_roles = parsed_profile.get('roles') or []

            selected_role = _normalize_role_input(role_input) if role_input else ''
            if not selected_role and parsed_roles:
                selected_role = _normalize_role_input(parsed_roles[0])

            required = ROLE_REQUIREMENTS.get(selected_role, []) if selected_role else []
            matched = [skill for skill in required if skill in extracted_skills]
            missing = [skill for skill in required if skill not in extracted_skills]

            score_normalized = 0.0
            if required:
                score_normalized = round(len(matched) / len(required), 2)
            elif extracted_skills:
                score_normalized = 0.5

            bucket = max(1, min(5, round(score_normalized * 5))) if score_normalized else 1

            explanation = (
                f"Evaluation based on extracted resume skills for role '{selected_role}'."
                if selected_role
                else 'Evaluation based on extracted resume skills. Provide ?role=... for tighter matching.'
            )

            return Response(
                {
                    'reference_no': reference_no,
                    'selected_role': selected_role or None,
                    'score_normalized': score_normalized,
                    'score_bucket': bucket,
                    'explanation': explanation,
                    'matched_skills': matched,
                    'missing_skills': missing,
                    'extracted_skills': extracted_skills,
                },
                status=status.HTTP_200_OK,
            )

        candidate = CANDIDATE_SCORES.get(reference_no)
        if not candidate:
            return Response(
                {
                    'detail': 'Candidate reference not found.',
                    'reference_no': reference_no,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(candidate, status=status.HTTP_200_OK)


class CandidateDeAnonymizeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, reference_no: str):
        candidate = CANDIDATE_SCORES.get(reference_no)
        if not candidate:
            return Response(
                {
                    'detail': 'Candidate reference not found.',
                    'reference_no': reference_no,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        reason = str(request.data.get('reason', '')).strip()
        if len(reason) < 10:
            return Response(
                {'detail': 'Reason must be at least 10 characters.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                'status': 'submitted',
                'reference_no': reference_no,
                'reason': reason,
                'message': 'De-anonymization request accepted and recorded for governance review.',
            },
            status=status.HTTP_202_ACCEPTED,
        )


class StudentRecommendationsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id: str):
        payload = STUDENT_RECOMMENDATIONS.get(user_id)
        if not payload:
            payload = STUDENT_RECOMMENDATIONS['student-demo-001']
        return Response(payload, status=status.HTTP_200_OK)
