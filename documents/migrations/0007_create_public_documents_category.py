from django.db import migrations


def create_public_documents_category(apps, schema_editor):
    DocumentCategory = apps.get_model('documents', 'DocumentCategory')
    if not DocumentCategory.objects.filter(is_public=True).exists():
        DocumentCategory.objects.get_or_create(
            name='Public Documents',
            defaults={
                'description': 'Documents available for anyone to download from the Resources page.',
                'is_public': True,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ('documents', '0006_documentcategory_is_public'),
    ]

    operations = [
        migrations.RunPython(create_public_documents_category, migrations.RunPython.noop),
    ]
