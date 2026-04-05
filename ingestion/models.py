from django.db import models


class ResumeUploadRecord(models.Model):
	STATUS_CHOICES = [
		('url_issued', 'Upload URL Issued'),
		('uploaded', 'Uploaded'),
		('parsed', 'Parsed'),
		('failed', 'Failed'),
	]

	reference_no = models.CharField(max_length=20, primary_key=True)
	original_filename = models.CharField(max_length=255)
	content_type = models.CharField(max_length=120, blank=True, default='')
	storage_backend = models.CharField(max_length=20, default='local')
	storage_key = models.TextField(blank=True, default='')
	object_size = models.BigIntegerField(null=True, blank=True)
	object_etag = models.CharField(max_length=255, blank=True, default='')
	parsed_json = models.JSONField(null=True, blank=True)
	parsed_at = models.DateTimeField(null=True, blank=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='url_issued')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'resume_upload_record'
		indexes = [
			models.Index(fields=['status']),
			models.Index(fields=['created_at']),
		]

	def __str__(self):
		return f"ResumeUploadRecord({self.reference_no}, {self.status})"