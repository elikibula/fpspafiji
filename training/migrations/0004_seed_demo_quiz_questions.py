from django.db import migrations


def seed_quiz_questions(apps, schema_editor):
    Course = apps.get_model("training", "Course")
    QuizQuestion = apps.get_model("training", "QuizQuestion")

    questions_by_course = {
        "Instructional Leadership for Primary School Excellence": [
            {
                "question_text": "Which leadership practice most directly supports improvement in classroom teaching?",
                "option_a": "Avoiding observation so teachers feel independent",
                "option_b": "Using structured observation and feedback cycles",
                "option_c": "Delegating all instructional decisions away from the principal",
                "option_d": "Focusing only on end-of-year reporting",
                "correct_option": "B",
                "explanation": "Observation and feedback cycles help principals support teaching quality in practical ways.",
            },
            {
                "question_text": "What is the best use of school data in instructional leadership?",
                "option_a": "Using it to identify priorities and guide improvement actions",
                "option_b": "Collecting it without discussion",
                "option_c": "Keeping it only for external compliance",
                "option_d": "Using it only at the end of the year",
                "correct_option": "A",
                "explanation": "Effective leaders use evidence to set priorities and monitor improvement.",
            },
        ],
        "School Governance and Compliance Workshop": [
            {
                "question_text": "Which practice strengthens governance accountability?",
                "option_a": "Leaving action items undocumented",
                "option_b": "Keeping clear decisions, records, and follow-up actions",
                "option_c": "Reducing oversight on school processes",
                "option_d": "Avoiding scheduled governance reviews",
                "correct_option": "B",
                "explanation": "Good governance depends on clear records and follow-through.",
            },
            {
                "question_text": "Why is a school compliance checklist valuable?",
                "option_a": "It replaces all leadership judgement",
                "option_b": "It ensures critical obligations are reviewed consistently",
                "option_c": "It removes the need for documentation",
                "option_d": "It is useful only for finance",
                "correct_option": "B",
                "explanation": "Checklists improve consistency and reduce missed obligations.",
            },
        ],
        "Digital Administration and Reporting for School Leaders": [
            {
                "question_text": "What is a strong first step in improving digital administration?",
                "option_a": "Adopting multiple tools without a plan",
                "option_b": "Designing simple, shared workflows and templates",
                "option_c": "Removing all documentation processes",
                "option_d": "Restricting communication to paper only",
                "correct_option": "B",
                "explanation": "Shared workflows and templates create consistency and clarity.",
            },
            {
                "question_text": "Why do reporting structures matter in school leadership?",
                "option_a": "They make communication less transparent",
                "option_b": "They help staff know what to report, when, and to whom",
                "option_c": "They eliminate the need for meetings",
                "option_d": "They are only useful for external audiences",
                "correct_option": "B",
                "explanation": "Clear structures improve communication and accountability.",
            },
        ],
    }

    for course_title, questions in questions_by_course.items():
        course = Course.objects.filter(title=course_title).first()
        if not course:
            continue
        for order, question in enumerate(questions, start=1):
            QuizQuestion.objects.get_or_create(
                course=course,
                order=order,
                defaults=question,
            )


def unseed_quiz_questions(apps, schema_editor):
    Course = apps.get_model("training", "Course")
    QuizQuestion = apps.get_model("training", "QuizQuestion")
    titles = [
        "Instructional Leadership for Primary School Excellence",
        "School Governance and Compliance Workshop",
        "Digital Administration and Reporting for School Leaders",
    ]
    courses = Course.objects.filter(title__in=titles)
    QuizQuestion.objects.filter(course__in=courses).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("training", "0003_quizattempt_quizquestion_workshopattendance"),
    ]

    operations = [
        migrations.RunPython(seed_quiz_questions, unseed_quiz_questions),
    ]
