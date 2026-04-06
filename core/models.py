"""
SRS 3.1: Canonical Tables for Split-Data Architecture

Implements Primary_Profile, Reference_Profile, Mapping_Table, and Audit_Log
per SRS 2.1 (Split-Data Flow) and SRS 3.1 (Canonical Tables).

Trust Boundary: AI services CANNOT query Primary_Profile directly.
Only Reintegration Service can resolve Reference_No to User_ID.
"""

import uuid
import logging
from django.db import models
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

try:
    from pgvector.django import VectorField
except Exception as exc:
    class VectorField(models.JSONField):
        """
        Compatibility fallback when pgvector (or numpy dependency) is unavailable.
        Stores vectors as JSON arrays so the app can run in restricted environments.
        """

        def __init__(self, *args, dimensions=None, **kwargs):
            self.dimensions = dimensions
            super().__init__(*args, **kwargs)

    logger.warning(
        "pgvector unavailable; using JSON fallback for VectorField. "
        "Vector index/search features may be degraded. Error: %s",
        exc,
    )


class PrimaryProfile(models.Model):
    """
    SRS FR-3.1: Persist raw and de-identified artifacts separately.
    
    Primary Store: Raw resume + PII metadata (encrypted at rest).
    FK to User for audit trail and identity binding.
    """
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Raw resume blob URI (S3, Azure Blob, etc.)
    resume_blob_uri = models.TextField(
        help_text="URI to encrypted raw resume (PDF/DOCX)"
    )
    
    # Encrypted PII JSON (AES-256 per SRS NFR-2.1)
    pii_json_encrypted = models.BinaryField(
        help_text="Encrypted JSON containing detected PII entities and confidence scores"
    )
    
    # Encryption metadata
    encryption_key_version = models.CharField(
        max_length=255,
        default='v1',
        help_text='KMS key version (SRS NFR-2.2: rotated every 90 days)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'primary_profile'
        indexes = [
            models.Index(fields=['created_at']),
        ]
        verbose_name_plural = 'Primary Profiles'
    
    def __str__(self):
        return f"PrimaryProfile({self.user_id})"


class ReferenceProfile(models.Model):
    """
    SRS FR-4.1, FR-4.2: De-identified profile + embedding vector.
    
    Reference Store: AI-facing records with NO PII by design.
    Linked to Primary via Mapping_Table (indirection layer for trust).
    
    SRS 3.3: Must store model_version and embedding_version for contract enforcement.
    """
    RESULT_STATUS_CHOICES = [
        ('pending', 'Pending Processing'),
        ('processed', 'Successfully Processed'),
        ('failed', 'Processing Failed'),
        ('blocked', 'Blocked: PII Leakage'),
    ]
    
    reference_no = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # De-identified profile JSON (SRS NFR-3.4: NO PII in reference store)
    profile_json = models.JSONField(
        help_text='De-identified structured profile: skills, roles, years_exp, projects, education'
    )
    
    # Embedding vector for semantic search (SRS 3.3: Embedding Contract)
    embedding_vector = VectorField(
        dimensions=1536,  # text-embedding-3-small dimension
        null=True,
        blank=True,
        help_text='Cosine-similarity vector for role matching'
    )
    
    # Scoring state (SRS FR-4.2, FR-4.3)
    result_status = models.CharField(
        max_length=20,
        choices=RESULT_STATUS_CHOICES,
        default='pending'
    )
    score_normalized = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Normalized similarity score in [0, 1]'
    )
    score_bucket = models.SmallIntegerField(
        null=True,
        blank=True,
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text='Recruiter-facing score bucket (1..5)'
    )
    
    # Explanation JSON (SRS FR-4.4: Evidence snippets + missing skills)
    explanation_json = models.JSONField(
        null=True,
        blank=True,
        help_text='Evidence spans, matched skills, missing skills, confidence breakdown'
    )
    
    # Model versioning (SRS 3.3: Re-embedding required on model_version change)
    model_version = models.CharField(
        max_length=50,
        default='v1.0',
        help_text='AI model version (e.g., semantic-ranker-v1, llama2-v2)'
    )
    embedding_version = models.CharField(
        max_length=50,
        default='text-embedding-3-small',
        help_text='Embedding model version (SRS 3.3: Must match for similarity comparison)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reference_profile'
        indexes = [
            models.Index(fields=['embedding_version', 'model_version']),
            models.Index(fields=['result_status']),
            models.Index(fields=['created_at']),
        ]
        verbose_name_plural = 'Reference Profiles'
    
    def __str__(self):
        return f"ReferenceProfile({self.reference_no}, status={self.result_status})"


class MappingTable(models.Model):
    """
    SRS FR-3.1, FR-3.2, FR-3.3: Mapping indirection layer.
    
    Creates exactly one mapping record per reference profile.
    This table is the ONLY bridge that AI modules can query to access user context.
    
    Trust Boundary: Only Reintegration Service can use this table to join results.
    AI services operate in 'blind' mode with reference_no only.
    """
    reference_no = models.OneToOneField(
        ReferenceProfile,
        on_delete=models.CASCADE,
        primary_key=True,
        help_text='Foreign key to de-identified profile'
    )
    
    user_id = models.UUIDField(
        help_text='Foreign key to primary profile (UUID)'
    )
    
    # Foreign key constraint would require PrimaryProfile to use UU IDField
    # Created manually in migration to avoid circular dependency issues
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'mapping_table'
        indexes = [
            models.Index(fields=['user_id']),
        ]
        verbose_name_plural = 'Mapping Table'
        unique_together = [['user_id', 'reference_no']]
    
    def __str__(self):
        return f"Mapping({self.reference_no} <- {self.user_id})"


class AuditLog(models.Model):
    """
    SRS FR-6.3, NFR-3.3, NFR-5.4: Immutable audit trail.
    
    Log all split, score, de-anonymize, and override events.
    Retention: 6-12 months (configurable per SRS NFR-3.3).
    Emit structured logs with correlation_id (SRS NFR-5.4).
    """
    EVENT_TYPE_CHOICES = [
        ('split_created', 'Split-Data Record Created'),
        ('pii_redacted', 'PII Redaction Pass'),
        ('scoring_complete', 'Scoring Complete'),
        ('deanonymize_requested', 'De-anonymization Requested'),
        ('deanonymize_approved', 'De-anonymization Approved'),
        ('deanonymize_denied', 'De-anonymization Denied'),
        ('score_override', 'Score Override'),
        ('model_changed', 'Model Version Changed'),
    ]
    
    ACTOR_ROLE_CHOICES = [
        ('recruiter', 'Recruiter'),
        ('student', 'Student'),
        ('admin', 'Administrator'),
        ('system', 'System Service'),
    ]
    
    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Actor information
    actor_id = models.UUIDField(
        help_text='User ID or service principal identifier'
    )
    actor_role = models.CharField(
        max_length=20,
        choices=ACTOR_ROLE_CHOICES
    )
    
    # Event classification
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPE_CHOICES
    )
    
    # Record references (nullable for system-level events)
    reference_no = models.UUIDField(
        null=True,
        blank=True,
        help_text='De-identified profile identifier'
    )
    user_id = models.UUIDField(
        null=True,
        blank=True,
        help_text='User identifier (if event is user-bound)'
    )
    
    # Mandatory reason field for sensitive operations (SRS FR-6.2)
    reason = models.TextField(
        help_text='Mandatory justification for de-anonymize and override events'
    )
    
    # Event payload (structured context)
    event_payload = models.JSONField(
        default=dict,
        help_text='JSON context: scores, decisions, policy checks'
    )
    
    # Correlation ID for tracing (SRS NFR-5.1)
    correlation_id = models.CharField(
        max_length=255,
        default='',
        help_text='Trace ID for request correlation across services'
    )
    
    # Timestamp (immutable after creation)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_log'
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['actor_role']),
            models.Index(fields=['reference_no']),
            models.Index(fields=['user_id']),
            models.Index(fields=['correlation_id']),
        ]
        verbose_name_plural = 'Audit Logs'
        # Prevent accidental updates
        permissions = [
            ('view_audit_log', 'Can view audit log'),
        ]
    
    def __str__(self):
        return f"AuditLog({self.event_type}, actor={self.actor_role})"
