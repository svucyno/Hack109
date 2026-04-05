from django.urls import path

from .views import ResumeParseView, ResumeRegisterUploadView, ResumeUploadUrlView, ResumeUploadView

urlpatterns = [
    path('upload', ResumeUploadView.as_view(), name='resume-upload'),
    path('upload-url', ResumeUploadUrlView.as_view(), name='resume-upload-url'),
    path('register-upload', ResumeRegisterUploadView.as_view(), name='resume-register-upload'),
    path('<str:reference_no>/parse', ResumeParseView.as_view(), name='resume-parse'),
]
