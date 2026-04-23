import uuid

from django.db import migrations, models


def populate_schedule_qr_tokens(apps, schema_editor):
    CourseSchedule = apps.get_model("training", "CourseSchedule")
    for schedule in CourseSchedule.objects.filter(attendance_qr_token__isnull=True):
        schedule.attendance_qr_token = uuid.uuid4()
        schedule.save(update_fields=["attendance_qr_token"])


class Migration(migrations.Migration):
    dependencies = [
        ("training", "0004_seed_demo_quiz_questions"),
    ]

    operations = [
        migrations.AddField(
            model_name="courseschedule",
            name="attendance_qr_token",
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name="courseschedule",
            name="qr_checkin_enabled",
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(populate_schedule_qr_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="courseschedule",
            name="attendance_qr_token",
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
    ]
