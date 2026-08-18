from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='LiveStream',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('stream_url', models.URLField(max_length=500)),
                ('platform', models.CharField(choices=[('youtube', 'YouTube'), ('facebook', 'Facebook')], editable=False, max_length=20)),
                ('event_date', models.DateTimeField(blank=True, null=True)),
                ('is_live', models.BooleanField(default=False)),
                ('is_featured', models.BooleanField(default=False)),
                ('is_published', models.BooleanField(default=True)),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to='livestream/thumbnails/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ('-event_date', '-created_at')},
        ),
    ]
