from datetime import timedelta

from django.db import migrations
from django.template.defaultfilters import slugify
from django.utils import timezone


def seed_demo_courses(apps, schema_editor):
    Course = apps.get_model("training", "Course")
    CourseSchedule = apps.get_model("training", "CourseSchedule")
    Module = apps.get_model("training", "Module")
    Lesson = apps.get_model("training", "Lesson")
    User = apps.get_model("accounts", "CustomUser")

    creator = (
        User.objects.filter(role__in=["admin", "staff"]).order_by("id").first()
        or User.objects.filter(is_superuser=True).order_by("id").first()
    )

    now = timezone.now()

    demo_courses = [
        {
            "title": "Instructional Leadership for Primary School Excellence",
            "short_description": "A practical online course for principals leading stronger teaching, assessment, and school improvement.",
            "description": "This FPSPA program helps primary school leaders strengthen instructional supervision, coaching conversations, classroom observation practice, and evidence-based improvement planning.",
            "learning_outcomes": "Lead professional conversations with confidence.\nUse school data for improvement planning.\nStrengthen classroom observation and support routines.",
            "target_audience": "Primary school principals, acting principals, and senior leadership teams.",
            "duration_hours": 8,
            "delivery_type": "online",
            "is_featured": True,
            "modules": [
                {
                    "title": "Leading Teaching and Learning",
                    "overview": "Core leadership moves that influence classroom practice and student outcomes.",
                    "lessons": [
                        ("Setting instructional priorities", 20),
                        ("Using evidence to guide decisions", 25),
                    ],
                },
                {
                    "title": "Coaching and Feedback",
                    "overview": "Practical frameworks for observation and growth-focused feedback.",
                    "lessons": [
                        ("Observation walkthroughs", 18),
                        ("Feedback conversations that improve practice", 22),
                    ],
                },
            ],
            "schedules": [
                ("Term 2 Online Cohort", "Zoom", now + timedelta(days=7), now + timedelta(days=7, hours=2)),
            ],
        },
        {
            "title": "School Governance and Compliance Workshop",
            "short_description": "A workshop series focused on governance, policy compliance, documentation, and operational readiness.",
            "description": "Built for FPSPA members who need a sharper operational toolkit, this workshop covers school governance responsibilities, policy execution, reporting discipline, and risk awareness.",
            "learning_outcomes": "Strengthen governance processes.\nImprove compliance documentation.\nBuild a practical school operations checklist.",
            "target_audience": "Principals, deputy principals, and school management teams.",
            "duration_hours": 6,
            "delivery_type": "workshop",
            "is_featured": True,
            "modules": [
                {
                    "title": "Governance Foundations",
                    "overview": "Roles, responsibilities, and meeting discipline for effective school governance.",
                    "lessons": [
                        ("Governance roles and accountability", 30),
                        ("Meeting records and action tracking", 20),
                    ],
                },
                {
                    "title": "Compliance in Practice",
                    "overview": "Policies, documentation, and readiness routines.",
                    "lessons": [
                        ("Compliance essentials", 25),
                        ("Operational readiness checklist", 20),
                    ],
                },
            ],
            "schedules": [
                ("Suva Workshop Session", "FPSPA Office, Suva", now + timedelta(days=14), now + timedelta(days=14, hours=4)),
                ("Western Division Workshop", "Lautoka", now + timedelta(days=21), now + timedelta(days=21, hours=4)),
            ],
        },
        {
            "title": "Digital Administration and Reporting for School Leaders",
            "short_description": "A blended learning program for principals improving digital workflows, reporting quality, and communication systems.",
            "description": "This blended FPSPA course supports principals in building reliable digital routines for communication, reporting, records management, and staff coordination.",
            "learning_outcomes": "Improve digital record keeping.\nStrengthen reporting processes.\nUse shared tools for team coordination.",
            "target_audience": "Principals and school administrators looking to modernize daily operations.",
            "duration_hours": 10,
            "delivery_type": "blended",
            "is_featured": False,
            "modules": [
                {
                    "title": "Digital Workflow Design",
                    "overview": "Organising tools, templates, and routines for efficient school administration.",
                    "lessons": [
                        ("Designing simple digital workflows", 20),
                        ("Shared templates and document control", 20),
                    ],
                },
                {
                    "title": "Reporting and Communication",
                    "overview": "Consistent reporting practices and communication systems for leadership teams.",
                    "lessons": [
                        ("Clear reporting structures", 25),
                        ("Communication systems for staff and community", 25),
                    ],
                },
            ],
            "schedules": [
                ("Blended Cohort Launch", "Online + regional support", now + timedelta(days=10), now + timedelta(days=10, hours=2)),
            ],
        },
    ]

    for course_data in demo_courses:
        course, created = Course.objects.get_or_create(
            title=course_data["title"],
            defaults={
                "slug": slugify(course_data["title"])[:50],
                "short_description": course_data["short_description"],
                "description": course_data["description"],
                "learning_outcomes": course_data["learning_outcomes"],
                "target_audience": course_data["target_audience"],
                "duration_hours": course_data["duration_hours"],
                "delivery_type": course_data["delivery_type"],
                "passing_score": 100,
                "is_published": True,
                "is_featured": course_data["is_featured"],
                "created_by_id": creator.id if creator else None,
            },
        )

        if not created:
            continue

        for module_index, module_data in enumerate(course_data["modules"], start=1):
            module = Module.objects.create(
                course=course,
                title=module_data["title"],
                overview=module_data["overview"],
                order=module_index,
            )
            for lesson_index, (lesson_title, duration_minutes) in enumerate(module_data["lessons"], start=1):
                Lesson.objects.create(
                    module=module,
                    title=lesson_title,
                    content=f"Demo training content for {lesson_title}. Replace this with your full FPSPA lesson material.",
                    duration_minutes=duration_minutes,
                    order=lesson_index,
                    is_preview=(lesson_index == 1 and module_index == 1),
                )

        for schedule_title, location, start_dt, end_dt in course_data["schedules"]:
            CourseSchedule.objects.create(
                course=course,
                title=schedule_title,
                location=location,
                facilitator="FPSPA Professional Learning Team",
                start_datetime=start_dt,
                end_datetime=end_dt,
                registration_deadline=start_dt - timedelta(days=2),
                capacity=30,
                notes="Demo seeded schedule for training showcase.",
                is_active=True,
            )


def unseed_demo_courses(apps, schema_editor):
    Course = apps.get_model("training", "Course")
    titles = [
        "Instructional Leadership for Primary School Excellence",
        "School Governance and Compliance Workshop",
        "Digital Administration and Reporting for School Leaders",
    ]
    Course.objects.filter(title__in=titles).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("training", "0001_initial"),
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_demo_courses, unseed_demo_courses),
    ]
