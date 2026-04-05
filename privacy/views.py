import re
import uuid

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


REPORT_STORE: dict[str, dict] = {}

PII_PATTERNS = {
    'EMAIL_ADDRESS': re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'),
    'PHONE_NUMBER': re.compile(r'(?:\+\d{1,3}[\s\-]?)?(?:\d[\s\-]?){10,12}'),
    'URL': re.compile(r'https?://[^\s]+', re.IGNORECASE),
}


def _build_findings(text: str) -> list[dict]:
    findings: list[dict] = []
    for entity_type, pattern in PII_PATTERNS.items():
        for match in pattern.finditer(text):
            findings.append(
                {
                    'entity_type': entity_type,
                    'value': match.group(0),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.95,
                }
            )
    return findings


def _redact_text(text: str) -> tuple[str, list[dict]]:
    findings = _build_findings(text)
    redacted = text
    for finding in findings:
        redacted = redacted.replace(finding['value'], f"[{finding['entity_type']}_REDACTED]")
    return redacted, findings


class PrivacyRedactView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        text = str(request.data.get('text', '')).strip()
        raw_reference = request.data.get('reference_no', '')
        if raw_reference is None:
            raw_reference = ''
        reference_no = str(raw_reference).strip() or f"REF-{str(uuid.uuid4())[:8].upper()}"

        if not text:
            return Response(
                {'detail': "Field 'text' is required for redaction."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        redacted_text, findings = _redact_text(text)
        report = {
            'reference_no': reference_no,
            'entity_count': len(findings),
            'entities': findings,
            'blocked': len(findings) > 0,
            'summary': {
                'high_confidence_count': len([item for item in findings if item['confidence'] >= 0.7]),
            },
        }

        REPORT_STORE[reference_no] = report

        return Response(
            {
                'reference_no': reference_no,
                'redacted_text': redacted_text,
                'report': report,
            },
            status=status.HTTP_200_OK,
        )


class PrivacyReportView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, reference_no: str):
        report = REPORT_STORE.get(reference_no)
        if not report:
            return Response(
                {
                    'detail': 'Redaction report not found for reference.',
                    'reference_no': reference_no,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(report, status=status.HTTP_200_OK)


class PrivacyValidateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        text = str(request.data.get('text', '')).strip()
        if not text:
            return Response(
                {'detail': "Field 'text' is required for validation."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        threshold = settings.SPLIT_DATA_CONFIG.get('PII_HIGH_CONFIDENCE_THRESHOLD', 0.7)
        findings = _build_findings(text)
        unresolved = [item for item in findings if item['confidence'] >= threshold]

        if unresolved:
            return Response(
                {
                    'status': 'blocked',
                    'message': 'PII leakage validation failed.',
                    'unresolved_entities': unresolved,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                'status': 'passed',
                'message': 'No high-confidence PII leakage detected.',
            },
            status=status.HTTP_200_OK,
        )
