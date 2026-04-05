from django.urls import path

from .api_views import (
    AdminOverviewView,
    HrOverviewView,
    StudentOverviewView,
    AdminResumeRecordsView,
    AdminResumeRecordDetailView,
)
from .ai_views import (
    GeminiStatusView,
    CandidateAIEvaluationView,
    ResumeAIAnalysisView,
    CareerRecommendationsView,
)

urlpatterns = [
    path('hr', HrOverviewView.as_view(), name='hr-overview'),
    path('student', StudentOverviewView.as_view(), name='student-overview'),
    path('admin', AdminOverviewView.as_view(), name='admin-overview'),
    path('admin/records', AdminResumeRecordsView.as_view(), name='admin-resume-records'),
    path('admin/records/<str:reference_no>', AdminResumeRecordDetailView.as_view(), name='admin-resume-record-detail'),
    
    # AI Evaluation Endpoints (Gemini-powered)
    path('ai/status', GeminiStatusView.as_view(), name='gemini-status'),
    path('candidates/<str:reference_no>/ai-evaluation', CandidateAIEvaluationView.as_view(), name='candidate-ai-evaluation'),
    path('candidates/<str:reference_no>/ai-analysis', ResumeAIAnalysisView.as_view(), name='resume-ai-analysis'),
    path('candidates/<str:reference_no>/career-recommendations', CareerRecommendationsView.as_view(), name='career-recommendations'),
]
