from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ingestion', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='resumeuploadrecord',
            name='object_etag',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='resumeuploadrecord',
            name='object_size',
            field=models.BigIntegerField(blank=True, null=True),
        ),
    ]
