import uuid

from django.conf import settings
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone


class Course(models.Model):
    DELIVERY_CHOICES = [
        ("online", "Online"),
        ("workshop", "Workshop"),
        ("blended", "Blended"),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    short_description = models.CharField(max_length=300)
    description = models.TextField()
    learning_outcomes = models.TextField(blank=True)
    target_audience = models.CharField(max_length=255, blank=True)
    duration_hours = models.PositiveIntegerField(default=1)
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default="online")
    passing_score = models.PositiveIntegerField(default=100)
    thumbnail = models.ImageField(upload_to="training/course_thumbnails/", blank=True, null=True)
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="training_courses_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "course"
            slug = base_slug
            suffix = 1
            while Course.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                suffix += 1
                slug = f"{base_slug}-{suffix}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("training:course_detail", kwargs={"slug": self.slug})

    @property
    def lesson_count(self):
        return Lesson.objects.filter(module__course=self).count()

    @property
    def quiz_question_count(self):
        return self.quiz_questions.count()


class CourseSchedule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="schedules")
    title = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    meeting_link = models.URLField(blank=True)
    facilitator = models.CharField(max_length=255, blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    registration_deadline = models.DateTimeField(blank=True, null=True)
    capacity = models.PositiveIntegerField(blank=True, null=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    attendance_qr_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    qr_checkin_enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ["start_datetime"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    @property
    def seats_remaining(self):
        if not self.capacity:
            return None
        enrolled_count = self.enrollments.filter(status__in=["enrolled", "completed"]).count()
        return max(self.capacity - enrolled_count, 0)


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=255)
    overview = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("course", "order")]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=255)
    content = models.TextField()
    resource_file = models.FileField(upload_to="training/lesson_resources/", blank=True, null=True)
    video_url = models.URLField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=10)
    order = models.PositiveIntegerField(default=1)
    is_preview = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("module", "order")]

    def __str__(self):
        return f"{self.module.title} - {self.title}"


class Enrollment(models.Model):
    STATUS_CHOICES = [
        ("enrolled", "Enrolled"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    member = models.ForeignKey("membership.Member", on_delete=models.CASCADE, related_name="training_enrollments")
    selected_schedule = models.ForeignKey(
        CourseSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enrollments",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="enrolled")
    progress_percent = models.PositiveIntegerField(default=0)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    last_accessed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-enrolled_at"]
        unique_together = [("course", "member")]

    def __str__(self):
        return f"{self.member.full_name} - {self.course.title}"

    def update_progress(self, save=True):
        total_lessons = Lesson.objects.filter(module__course=self.course).count()
        completed_lessons = self.lesson_progress.filter(is_completed=True).count()
        if total_lessons == 0:
            self.progress_percent = 0
        else:
            self.progress_percent = round((completed_lessons / total_lessons) * 100)

        lesson_requirement_met = total_lessons == 0 or completed_lessons == total_lessons

        passed_quiz_required = True
        if self.course.quiz_questions.exists():
            passed_quiz_required = self.quiz_attempts.filter(passed=True).exists()

        attendance_requirement_met = True
        if self.selected_schedule_id:
            attendance_requirement_met = self.attendance_records.filter(
                schedule=self.selected_schedule,
                status="attended",
            ).exists()

        if lesson_requirement_met and passed_quiz_required and attendance_requirement_met:
            self.status = "completed"
            if not self.completed_at:
                self.completed_at = timezone.now()
        elif self.status != "cancelled":
            self.status = "enrolled"
            self.completed_at = None

        self.last_accessed_at = timezone.now()
        if save:
            self.save(update_fields=["progress_percent", "status", "completed_at", "last_accessed_at"])
        return self.progress_percent

    @property
    def passed_quiz(self):
        if not self.course.quiz_questions.exists():
            return True
        return self.quiz_attempts.filter(passed=True).exists()

    @property
    def latest_quiz_attempt(self):
        return self.quiz_attempts.order_by("-attempted_at").first()


class LessonProgress(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress_entries")
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = [("enrollment", "lesson")]
        ordering = ["lesson__module__order", "lesson__order"]

    def __str__(self):
        return f"{self.enrollment} - {self.lesson}"


class Certificate(models.Model):
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name="certificate")
    certificate_number = models.CharField(max_length=50, unique=True, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="training_certificates_issued",
    )

    class Meta:
        ordering = ["-issued_at"]

    def __str__(self):
        return f"{self.certificate_number} - {self.enrollment.member.full_name}"

    def save(self, *args, **kwargs):
        if not self.certificate_number:
            timestamp = timezone.now().strftime("%Y%m%d")
            base_number = f"FHTA-CERT-{timestamp}"
            candidate = base_number
            suffix = 1
            while Certificate.objects.exclude(pk=self.pk).filter(certificate_number=candidate).exists():
                suffix += 1
                candidate = f"{base_number}-{suffix}"
            self.certificate_number = candidate
        super().save(*args, **kwargs)


class QuizQuestion(models.Model):
    OPTION_CHOICES = [
        ("A", "Option A"),
        ("B", "Option B"),
        ("C", "Option C"),
        ("D", "Option D"),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="quiz_questions")
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255, blank=True)
    option_d = models.CharField(max_length=255, blank=True)
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES)
    explanation = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("course", "order")]

    def __str__(self):
        return f"{self.course.title} - Question {self.order}"


class QuizAttempt(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="quiz_attempts")
    score = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    passed = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-attempted_at"]

    def __str__(self):
        return f"{self.enrollment} - {self.score}%"


class WorkshopAttendance(models.Model):
    ATTENDANCE_CHOICES = [
        ("registered", "Registered"),
        ("attended", "Attended"),
        ("absent", "Absent"),
    ]

    schedule = models.ForeignKey(CourseSchedule, on_delete=models.CASCADE, related_name="attendance_records")
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="attendance_records")
    status = models.CharField(max_length=20, choices=ATTENDANCE_CHOICES, default="registered")
    marked_at = models.DateTimeField(blank=True, null=True)
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="training_attendance_marked",
    )
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["schedule__start_datetime", "enrollment__member__last_name"]
        unique_together = [("schedule", "enrollment")]

    def __str__(self):
        return f"{self.schedule} - {self.enrollment.member.full_name}"
