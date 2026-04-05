from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ResumeUploadRecord',
            fields=[
                ('reference_no', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('original_filename', models.CharField(max_length=255)),
                ('content_type', models.CharField(blank=True, default='', max_length=120)),
                ('storage_backend', models.CharField(default='local', max_length=20)),
                ('storage_key', models.TextField(blank=True, default='')),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('url_issued', 'Upload URL Issued'),
                            ('uploaded', 'Uploaded'),
                            ('parsed', 'Parsed'),
                            ('failed', 'Failed'),
                        ],
                        default='url_issued',
                        max_length=20,
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'resume_upload_record',
            },
        ),
        migrations.AddIndex(
            model_name='resumeuploadrecord',
            index=models.Index(fields=['status'], name='resume_uplo_status_137061_idx'),
        ),
        migrations.AddIndex(
            model_name='resumeuploadrecord',
            index=models.Index(fields=['created_at'], name='resume_uplo_created_685891_idx'),
        ),
    ]
