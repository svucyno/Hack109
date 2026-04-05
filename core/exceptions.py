"""
Custom exception handlers and standardized error response formatting.
SRS FR-7.5: Endpoints shall emit standardized error schema.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom DRF exception handler returning standardized error schema.
    
    Response format:
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Human-readable message",
            "details": {...}
        }
    }
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        error_code = 'VALIDATION_ERROR'
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            error_code = 'UNAUTHORIZED'
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            error_code = 'FORBIDDEN'
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            error_code = 'NOT_FOUND'
        elif response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            error_code = 'INTERNAL_ERROR'
        
        response.data = {
            'error': {
                'code': error_code,
                'message': str(response.data),
                'details': response.data if isinstance(response.data, dict) else None
            }
        }
    
    return response
