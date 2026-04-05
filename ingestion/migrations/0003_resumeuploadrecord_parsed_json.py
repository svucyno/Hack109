from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ingestion', '0002_resumeuploadrecord_object_metadata'),
    ]

    operations = [
        migrations.AddField(
            model_name='resumeuploadrecord',
            name='parsed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='resumeuploadrecord',
            name='parsed_json',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
