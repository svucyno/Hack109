"""
URL configuration for GetHired project.
SRS FR-7.1: API shall expose versioned REST endpoints under /api/v1
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('_allauth/', include('allauth.headless.urls')),
    
    # Phase 1 and Phase 2 API surface.
    path('api/v1/', include('core.urls')),
    path('api/v1/resumes/', include('ingestion.urls')),
    path('api/v1/privacy/', include('privacy.urls')),
    path('api/v1/', include('matching.urls')),
]
