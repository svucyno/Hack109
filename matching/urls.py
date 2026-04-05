from django.urls import path

from .views import CandidateScoreView, CandidateDeAnonymizeView, StudentRecommendationsView

urlpatterns = [
    path('candidates/<str:reference_no>/score', CandidateScoreView.as_view(), name='candidate-score'),
    path('candidates/<str:reference_no>/deanonymize', CandidateDeAnonymizeView.as_view(), name='candidate-deanonymize'),
    path('students/<str:user_id>/recommendations', StudentRecommendationsView.as_view(), name='student-recommendations'),
]
