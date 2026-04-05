from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


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


class CandidateScoreView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, reference_no: str):
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
