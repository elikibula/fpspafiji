from django.db import migrations


REPLACEMENTS = (
    ("Fiji Primary School Principals Association", "Fiji Head Teachers Association"),
    ("Primary School Principals Association", "Head Teachers Association"),
    ("Principals Association", "Head Teachers Association"),
    ("FPSPA", "FHTA"),
    ("Principals", "Head Teachers"),
    ("Principal", "Head Teacher"),
    ("principals", "head teachers"),
    ("principal", "head teacher"),
    ("pricipals", "head teachers"),
    ("pricipal", "head teacher"),
)


def update_text(value):
    if not value:
        return value
    for old, new in REPLACEMENTS:
        value = value.replace(old, new)
    return value


def update_public_branding(apps, schema_editor):
    model_fields = (
        ("training", "Course", ("title", "short_description", "description", "learning_outcomes", "target_audience")),
        ("training", "CourseSchedule", ("title", "location", "facilitator", "notes")),
        ("training", "Module", ("title", "overview")),
        ("training", "Lesson", ("title", "content")),
        ("training", "QuizQuestion", ("question_text", "option_a", "option_b", "option_c", "option_d", "explanation")),
        ("news", "News", ("title", "content")),
        ("news", "PhotoNews", ("title", "description")),
    )

    for app_label, model_name, fields in model_fields:
        model = apps.get_model(app_label, model_name)
        for record in model.objects.all().iterator():
            changed_fields = []
            for field in fields:
                original = getattr(record, field)
                updated = update_text(original)
                if updated != original:
                    setattr(record, field, updated)
                    changed_fields.append(field)
            if changed_fields:
                record.save(update_fields=changed_fields)


class Migration(migrations.Migration):
    dependencies = [
        ("news", "0003_alter_photonews_image"),
        ("training", "0005_courseschedule_qr_fields"),
    ]

    operations = [
        migrations.RunPython(update_public_branding, migrations.RunPython.noop),
    ]
