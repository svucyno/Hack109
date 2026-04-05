from django.urls import path

from .views import PrivacyRedactView, PrivacyReportView, PrivacyValidateView

urlpatterns = [
    path('redact', PrivacyRedactView.as_view(), name='privacy-redact'),
    path('<str:reference_no>/report', PrivacyReportView.as_view(), name='privacy-report'),
    path('validate', PrivacyValidateView.as_view(), name='privacy-validate'),
]
