"""
URL configuration for GetHired project.
SRS FR-7.1: API shall expose versioned REST endpoints under /api/v1
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # JWT Authentication endpoints (SRS FR-7.6)
    path('api/v1/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Versioned API endpoints (SRS FR-7.1, FR-7.2, FR-7.3, FR-7.4)
    # To be populated in Phase 2-5:
    # path('api/v1/resumes/', include('ingestion.urls')),
    # path('api/v1/privacy/', include('privacy.urls')),
    # path('api/v1/candidates/', include('matching.urls')),
    # path('api/v1/students/', include('matching.urls')),
    # path('api/v1/governance/', include('governance.urls')),
]
