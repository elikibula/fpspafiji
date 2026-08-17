from django.db import migrations, models


def mark_existing_downloads_public(apps, schema_editor):
    DocumentCategory = apps.get_model('documents', 'DocumentCategory')
    DocumentCategory.objects.filter(name__iexact='Downloads').update(is_public=True)


class Migration(migrations.Migration):
    dependencies = [
        ('documents', '0005_documentcategory_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentcategory',
            name='is_public',
            field=models.BooleanField(
                default=False,
                help_text='Show documents in this folder on the public Resources page.',
            ),
        ),
        migrations.RunPython(mark_existing_downloads_public, migrations.RunPython.noop),
    ]
