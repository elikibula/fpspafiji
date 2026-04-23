from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from membership.models import Member

from .forms import CourseForm, CourseScheduleForm, LessonForm, ModuleForm, QuizQuestionForm
from .models import Certificate, Course, CourseSchedule, Enrollment, Lesson, LessonProgress, Module, QuizAttempt, QuizQuestion, WorkshopAttendance


def staff_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if getattr(request.user, "role", "") not in ["admin", "staff"] and not request.user.is_superuser:
            messages.error(request, "Staff access is required for training management.")
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return wrapped_view


def course_catalog(request):
    query = request.GET.get("q", "").strip()
    delivery = request.GET.get("delivery", "").strip()
    courses = Course.objects.filter(is_published=True).prefetch_related("modules", "schedules")

    if query:
        courses = courses.filter(
            Q(title__icontains=query)
            | Q(short_description__icontains=query)
            | Q(description__icontains=query)
        )
    if delivery:
        courses = courses.filter(delivery_type=delivery)

    featured_courses = courses.filter(is_featured=True)[:3]

    context = {
        "courses": courses,
        "featured_courses": featured_courses,
        "query": query,
        "delivery": delivery,
        "delivery_choices": Course.DELIVERY_CHOICES,
    }
    return render(request, "training/course_catalog.html", context)


def course_detail(request, slug):
    course = get_object_or_404(
        Course.objects.prefetch_related(
            Prefetch("modules", queryset=Module.objects.prefetch_related("lessons")),
            "schedules",
            "quiz_questions",
        ),
        slug=slug,
        is_published=True,
    )

    enrollment = None
    if request.user.is_authenticated:
        member = Member.objects.filter(user=request.user).first()
        if member:
            enrollment = Enrollment.objects.filter(course=course, member=member).first()

    schedules = course.schedules.filter(is_active=True)
    context = {
        "course": course,
        "enrollment": enrollment,
        "schedules": schedules,
    }
    return render(request, "training/course_detail.html", context)


def _get_member_or_redirect(request):
    member = Member.objects.filter(user=request.user).first()
    if not member:
        messages.warning(request, "Please complete your member profile before enrolling in training.")
        return None, redirect("complete_member_profile")
    return member, None


@login_required
def enroll_in_course(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    member, response = _get_member_or_redirect(request)
    if response:
        return response

    if request.method != "POST":
        return redirect("training:course_detail", slug=slug)

    selected_schedule = None
    schedule_id = request.POST.get("schedule_id")
    if schedule_id:
        selected_schedule = get_object_or_404(CourseSchedule, pk=schedule_id, course=course, is_active=True)
        seats_remaining = selected_schedule.seats_remaining
        if seats_remaining == 0:
            messages.error(request, "That workshop session is already full.")
            return redirect("training:course_detail", slug=slug)

    enrollment, created = Enrollment.objects.get_or_create(
        course=course,
        member=member,
        defaults={"selected_schedule": selected_schedule},
    )
    if not created and selected_schedule and enrollment.selected_schedule_id != selected_schedule.id:
        enrollment.selected_schedule = selected_schedule
        enrollment.save(update_fields=["selected_schedule"])

    if created:
        messages.success(request, f"You are now enrolled in {course.title}.")
    else:
        messages.info(request, f"You are already enrolled in {course.title}.")
    return redirect("training:my_learning")


@login_required
def my_learning(request):
    member, response = _get_member_or_redirect(request)
    if response:
        return response

    enrollments = (
        Enrollment.objects.filter(member=member)
        .select_related("course", "selected_schedule")
        .prefetch_related("lesson_progress", "course__modules__lessons", "quiz_attempts", "course__quiz_questions")
    )

    completed_count = enrollments.filter(status="completed").count()
    active_count = enrollments.filter(status="enrolled").count()

    context = {
        "enrollments": enrollments,
        "completed_count": completed_count,
        "active_count": active_count,
    }
    return render(request, "training/my_learning.html", context)


@login_required
def learning_detail(request, enrollment_id):
    member, response = _get_member_or_redirect(request)
    if response:
        return response

    enrollment = get_object_or_404(
        Enrollment.objects.select_related("course", "selected_schedule", "member")
        .prefetch_related(
            Prefetch("course__modules", queryset=Module.objects.prefetch_related("lessons")),
            "lesson_progress__lesson",
            "course__quiz_questions",
            "quiz_attempts",
        ),
        pk=enrollment_id,
        member=member,
    )

    progress_map = {
        progress.lesson_id: progress
        for progress in enrollment.lesson_progress.all()
    }
    enrollment.update_progress()

    context = {
        "enrollment": enrollment,
        "progress_map": progress_map,
        "quiz_questions": enrollment.course.quiz_questions.all(),
        "latest_quiz_attempt": enrollment.latest_quiz_attempt,
    }
    return render(request, "training/learning_detail.html", context)


@login_required
def mark_lesson_complete(request, enrollment_id, lesson_id):
    member, response = _get_member_or_redirect(request)
    if response:
        return response

    enrollment = get_object_or_404(Enrollment, pk=enrollment_id, member=member)
    lesson = get_object_or_404(Lesson, pk=lesson_id, module__course=enrollment.course)

    progress, created = LessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson,
        defaults={"is_completed": True, "completed_at": timezone.now()},
    )
    if not created and not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = timezone.now()
        progress.save(update_fields=["is_completed", "completed_at"])

    enrollment.update_progress()

    if enrollment.status == "completed" and not hasattr(enrollment, "certificate"):
        Certificate.objects.create(enrollment=enrollment)
        messages.success(request, f"Congratulations. You completed {enrollment.course.title} and your certificate is now available.")
    else:
        messages.success(request, f"Marked lesson '{lesson.title}' as completed.")

    return redirect("training:learning_detail", enrollment_id=enrollment.id)


@login_required
def submit_quiz(request, enrollment_id):
    member, response = _get_member_or_redirect(request)
    if response:
        return response

    enrollment = get_object_or_404(
        Enrollment.objects.select_related("course"),
        pk=enrollment_id,
        member=member,
    )
    questions = list(enrollment.course.quiz_questions.all())

    if request.method != "POST" or not questions:
        return redirect("training:learning_detail", enrollment_id=enrollment.id)

    correct_answers = 0
    for question in questions:
        selected = request.POST.get(f"question_{question.id}", "").strip().upper()
        if selected == question.correct_option:
            correct_answers += 1

    total_questions = len(questions)
    score = round((correct_answers / total_questions) * 100) if total_questions else 0
    passed = score >= enrollment.course.passing_score
    QuizAttempt.objects.create(
        enrollment=enrollment,
        score=score,
        total_questions=total_questions,
        passed=passed,
    )
    enrollment.update_progress()

    if enrollment.status == "completed" and not hasattr(enrollment, "certificate"):
        Certificate.objects.create(enrollment=enrollment)

    if passed:
        messages.success(request, f"You passed the course assessment with a score of {score}%.")
    else:
        messages.error(request, f"You scored {score}%. You need {enrollment.course.passing_score}% to pass.")

    return redirect("training:learning_detail", enrollment_id=enrollment.id)


@login_required
def certificate_detail(request, certificate_id):
    member, response = _get_member_or_redirect(request)
    if response:
        return response

    certificate = get_object_or_404(
        Certificate.objects.select_related("enrollment", "enrollment__course", "enrollment__member"),
        pk=certificate_id,
        enrollment__member=member,
    )
    return render(request, "training/certificate_detail.html", {"certificate": certificate})


@login_required
def certificate_print(request, certificate_id):
    member, response = _get_member_or_redirect(request)
    if response:
        return response

    certificate = get_object_or_404(
        Certificate.objects.select_related("enrollment", "enrollment__course", "enrollment__member"),
        pk=certificate_id,
        enrollment__member=member,
    )
    return render(request, "training/certificate_print.html", {"certificate": certificate})


@login_required
def attendance_checkin(request, schedule_id, token):
    schedule = get_object_or_404(
        CourseSchedule.objects.select_related("course"),
        pk=schedule_id,
        attendance_qr_token=token,
        qr_checkin_enabled=True,
        is_active=True,
    )
    member, response = _get_member_or_redirect(request)
    if response:
        return response

    enrollment = Enrollment.objects.filter(course=schedule.course, member=member).select_related("selected_schedule").first()
    if not enrollment:
        messages.error(request, "You must be enrolled in this training before you can check in.")
        return redirect("training:course_detail", slug=schedule.course.slug)

    if enrollment.selected_schedule_id and enrollment.selected_schedule_id != schedule.id:
        raise Http404("This QR code is for a different schedule.")

    if not enrollment.selected_schedule_id:
        enrollment.selected_schedule = schedule
        enrollment.save(update_fields=["selected_schedule"])

    attendance, created = WorkshopAttendance.objects.get_or_create(
        schedule=schedule,
        enrollment=enrollment,
        defaults={
            "status": "attended",
            "marked_at": timezone.now(),
            "marked_by": request.user,
        },
    )
    if not created:
        attendance.status = "attended"
        attendance.marked_at = timezone.now()
        attendance.marked_by = request.user
        attendance.save(update_fields=["status", "marked_at", "marked_by"])

    enrollment.update_progress()
    if enrollment.status == "completed" and not hasattr(enrollment, "certificate"):
        Certificate.objects.create(enrollment=enrollment, issued_by=request.user)

    return render(
        request,
        "training/attendance_checkin_success.html",
        {"schedule": schedule, "enrollment": enrollment},
    )


@staff_required
def staff_dashboard(request):
    courses = Course.objects.prefetch_related("modules", "schedules")
    enrollments = Enrollment.objects.select_related("course", "member")
    certificates = Certificate.objects.select_related("enrollment", "enrollment__course")
    upcoming_schedules = CourseSchedule.objects.filter(start_datetime__gte=timezone.now(), is_active=True).order_by("start_datetime")[:6]

    context = {
        "stats": {
            "total_courses": courses.count(),
            "published_courses": courses.filter(is_published=True).count(),
            "total_enrollments": enrollments.count(),
            "completed_enrollments": enrollments.filter(status="completed").count(),
            "certificates_issued": certificates.count(),
        },
        "recent_courses": courses.order_by("-updated_at")[:5],
        "upcoming_schedules": upcoming_schedules,
    }
    return render(request, "training/staff_dashboard.html", context)


@staff_required
def staff_course_list(request):
    courses = (
        Course.objects.annotate(
            module_total=Count("modules", distinct=True),
            schedule_total=Count("schedules", distinct=True),
            enrollment_total=Count("enrollments", distinct=True),
        )
        .order_by("title")
    )
    return render(request, "training/staff_course_list.html", {"courses": courses})


@staff_required
def staff_course_create(request):
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.created_by = request.user
            course.save()
            messages.success(request, f"Created training course '{course.title}'.")
            return redirect("training:staff_course_detail", course_id=course.id)
    else:
        form = CourseForm()
    return render(request, "training/staff_course_form.html", {"form": form, "page_title": "Create Course"})


@staff_required
def staff_course_edit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated training course '{course.title}'.")
            return redirect("training:staff_course_detail", course_id=course.id)
    else:
        form = CourseForm(instance=course)
    return render(
        request,
        "training/staff_course_form.html",
        {"form": form, "course": course, "page_title": f"Edit {course.title}"},
    )


@staff_required
def staff_course_detail(request, course_id):
    course = get_object_or_404(
        Course.objects.prefetch_related(
            Prefetch("modules", queryset=Module.objects.prefetch_related("lessons")),
            "schedules",
            "enrollments__member",
            "quiz_questions",
        ),
        pk=course_id,
    )

    module_form = ModuleForm(prefix="module")
    schedule_form = CourseScheduleForm(prefix="schedule")
    quiz_form = QuizQuestionForm(prefix="quiz")
    lesson_forms = {module.id: LessonForm(prefix=f"lesson-{module.id}") for module in course.modules.all()}

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add_module":
            module_form = ModuleForm(request.POST, prefix="module")
            if module_form.is_valid():
                module = module_form.save(commit=False)
                module.course = course
                module.save()
                messages.success(request, f"Added module '{module.title}'.")
                return redirect("training:staff_course_detail", course_id=course.id)

        elif action == "add_schedule":
            schedule_form = CourseScheduleForm(request.POST, prefix="schedule")
            if schedule_form.is_valid():
                schedule = schedule_form.save(commit=False)
                schedule.course = course
                schedule.save()
                messages.success(request, f"Added schedule '{schedule.title}'.")
                return redirect("training:staff_course_detail", course_id=course.id)

        elif action == "add_lesson":
            module_id = request.POST.get("module_id")
            module = get_object_or_404(Module, pk=module_id, course=course)
            lesson_form = LessonForm(request.POST, request.FILES, prefix=f"lesson-{module.id}")
            lesson_forms[module.id] = lesson_form
            if lesson_form.is_valid():
                lesson = lesson_form.save(commit=False)
                lesson.module = module
                lesson.save()
                messages.success(request, f"Added lesson '{lesson.title}' to {module.title}.")
                return redirect("training:staff_course_detail", course_id=course.id)

        elif action == "add_quiz_question":
            quiz_form = QuizQuestionForm(request.POST, prefix="quiz")
            if quiz_form.is_valid():
                question = quiz_form.save(commit=False)
                question.course = course
                question.save()
                messages.success(request, "Added quiz question.")
                return redirect("training:staff_course_detail", course_id=course.id)

    enrollments = course.enrollments.select_related("member", "selected_schedule").order_by("-enrolled_at")
    context = {
        "course": course,
        "module_form": module_form,
        "schedule_form": schedule_form,
        "quiz_form": quiz_form,
        "lesson_forms": lesson_forms,
        "enrollments": enrollments,
        "lesson_media": LessonForm().media,
        "module_media": ModuleForm().media,
        "schedule_media": CourseScheduleForm().media,
        "quiz_media": QuizQuestionForm().media,
    }
    return render(request, "training/staff_course_detail.html", context)


@staff_required
def staff_module_edit(request, module_id):
    module = get_object_or_404(Module.objects.select_related("course"), pk=module_id)
    if request.method == "POST":
        form = ModuleForm(request.POST, instance=module)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated module '{module.title}'.")
            return redirect("training:staff_course_detail", course_id=module.course_id)
    else:
        form = ModuleForm(instance=module)
    return render(request, "training/staff_object_form.html", {"form": form, "page_title": f"Edit Module: {module.title}", "back_url": reverse("training:staff_course_detail", kwargs={"course_id": module.course_id})})


@staff_required
def staff_module_delete(request, module_id):
    module = get_object_or_404(Module.objects.select_related("course"), pk=module_id)
    course_id = module.course_id
    title = module.title
    if request.method == "POST":
        module.delete()
        messages.success(request, f"Deleted module '{title}'.")
        return redirect("training:staff_course_detail", course_id=course_id)
    return render(request, "training/staff_confirm_delete.html", {"object_name": title, "object_type": "module", "back_url": reverse("training:staff_course_detail", kwargs={"course_id": course_id})})


@staff_required
def staff_lesson_edit(request, lesson_id):
    lesson = get_object_or_404(Lesson.objects.select_related("module", "module__course"), pk=lesson_id)
    if request.method == "POST":
        form = LessonForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated lesson '{lesson.title}'.")
            return redirect("training:staff_course_detail", course_id=lesson.module.course_id)
    else:
        form = LessonForm(instance=lesson)
    return render(request, "training/staff_object_form.html", {"form": form, "page_title": f"Edit Lesson: {lesson.title}", "back_url": reverse("training:staff_course_detail", kwargs={"course_id": lesson.module.course_id})})


@staff_required
def staff_lesson_delete(request, lesson_id):
    lesson = get_object_or_404(Lesson.objects.select_related("module", "module__course"), pk=lesson_id)
    course_id = lesson.module.course_id
    title = lesson.title
    if request.method == "POST":
        lesson.delete()
        messages.success(request, f"Deleted lesson '{title}'.")
        return redirect("training:staff_course_detail", course_id=course_id)
    return render(request, "training/staff_confirm_delete.html", {"object_name": title, "object_type": "lesson", "back_url": reverse("training:staff_course_detail", kwargs={"course_id": course_id})})


@staff_required
def staff_schedule_edit(request, schedule_id):
    schedule = get_object_or_404(CourseSchedule.objects.select_related("course"), pk=schedule_id)
    if request.method == "POST":
        form = CourseScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated schedule '{schedule.title}'.")
            return redirect("training:staff_course_detail", course_id=schedule.course_id)
    else:
        form = CourseScheduleForm(instance=schedule)
    return render(request, "training/staff_object_form.html", {"form": form, "page_title": f"Edit Schedule: {schedule.title}", "back_url": reverse("training:staff_course_detail", kwargs={"course_id": schedule.course_id})})


@staff_required
def staff_schedule_delete(request, schedule_id):
    schedule = get_object_or_404(CourseSchedule.objects.select_related("course"), pk=schedule_id)
    course_id = schedule.course_id
    title = schedule.title
    if request.method == "POST":
        schedule.delete()
        messages.success(request, f"Deleted schedule '{title}'.")
        return redirect("training:staff_course_detail", course_id=course_id)
    return render(request, "training/staff_confirm_delete.html", {"object_name": title, "object_type": "schedule", "back_url": reverse("training:staff_course_detail", kwargs={"course_id": course_id})})


@staff_required
def staff_quiz_question_edit(request, question_id):
    question = get_object_or_404(QuizQuestion.objects.select_related("course"), pk=question_id)
    if request.method == "POST":
        form = QuizQuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, "Updated quiz question.")
            return redirect("training:staff_course_detail", course_id=question.course_id)
    else:
        form = QuizQuestionForm(instance=question)
    return render(request, "training/staff_object_form.html", {"form": form, "page_title": f"Edit Quiz Question #{question.order}", "back_url": reverse("training:staff_course_detail", kwargs={"course_id": question.course_id})})


@staff_required
def staff_quiz_question_delete(request, question_id):
    question = get_object_or_404(QuizQuestion.objects.select_related("course"), pk=question_id)
    course_id = question.course_id
    label = f"Question {question.order}"
    if request.method == "POST":
        question.delete()
        messages.success(request, "Deleted quiz question.")
        return redirect("training:staff_course_detail", course_id=course_id)
    return render(request, "training/staff_confirm_delete.html", {"object_name": label, "object_type": "quiz question", "back_url": reverse("training:staff_course_detail", kwargs={"course_id": course_id})})


@staff_required
def staff_schedule_attendance(request, schedule_id):
    schedule = get_object_or_404(
        CourseSchedule.objects.select_related("course").prefetch_related("enrollments__member"),
        pk=schedule_id,
    )
    enrollments = schedule.enrollments.select_related("member").order_by("member__last_name", "member__first_name")

    if request.method == "POST":
        for enrollment in enrollments:
            status = request.POST.get(f"attendance_{enrollment.id}", "registered")
            notes = request.POST.get(f"notes_{enrollment.id}", "").strip()
            attendance, _ = WorkshopAttendance.objects.get_or_create(
                schedule=schedule,
                enrollment=enrollment,
            )
            attendance.status = status
            attendance.notes = notes
            attendance.marked_by = request.user
            attendance.marked_at = timezone.now()
            attendance.save()
            enrollment.update_progress()
            if enrollment.status == "completed" and not hasattr(enrollment, "certificate"):
                Certificate.objects.create(enrollment=enrollment, issued_by=request.user)
        messages.success(request, f"Updated attendance for '{schedule.title}'.")
        return redirect("training:staff_schedule_attendance", schedule_id=schedule.id)

    attendance_map = {
        record.enrollment_id: record
        for record in schedule.attendance_records.select_related("enrollment")
    }
    checkin_url = request.build_absolute_uri(
        reverse("training:attendance_checkin", kwargs={"schedule_id": schedule.id, "token": schedule.attendance_qr_token})
    )
    return render(
        request,
        "training/staff_schedule_attendance.html",
        {
            "schedule": schedule,
            "enrollments": enrollments,
            "attendance_map": attendance_map,
            "attendance_choices": WorkshopAttendance.ATTENDANCE_CHOICES,
            "checkin_url": checkin_url,
        },
    )


@staff_required
def staff_schedule_qr_poster(request, schedule_id):
    schedule = get_object_or_404(
        CourseSchedule.objects.select_related("course"),
        pk=schedule_id,
    )
    checkin_url = request.build_absolute_uri(
        reverse("training:attendance_checkin", kwargs={"schedule_id": schedule.id, "token": schedule.attendance_qr_token})
    )
    return render(
        request,
        "training/staff_schedule_qr_poster.html",
        {
            "schedule": schedule,
            "checkin_url": checkin_url,
        },
    )
