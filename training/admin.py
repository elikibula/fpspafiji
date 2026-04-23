from django.contrib import admin

from .models import Certificate, Course, CourseSchedule, Enrollment, Lesson, LessonProgress, Module, QuizAttempt, QuizQuestion, WorkshopAttendance


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1


class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 1


class ModuleInline(admin.StackedInline):
    model = Module
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "delivery_type", "duration_hours", "is_published", "is_featured")
    list_filter = ("delivery_type", "is_published", "is_featured")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "short_description", "description")
    inlines = [ModuleInline, QuizQuestionInline]


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    list_filter = ("course",)
    search_fields = ("title", "course__title")
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "module", "duration_minutes", "order", "is_preview")
    list_filter = ("module__course", "is_preview")
    search_fields = ("title", "module__title", "module__course__title")


@admin.register(CourseSchedule)
class CourseScheduleAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "start_datetime", "end_datetime", "capacity", "is_active")
    list_filter = ("course", "is_active")
    search_fields = ("title", "course__title", "facilitator", "location")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("member", "course", "status", "progress_percent", "enrolled_at")
    list_filter = ("status", "course")
    search_fields = ("member__first_name", "member__last_name", "course__title", "member__membership_number")


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "lesson", "is_completed", "completed_at")
    list_filter = ("is_completed",)
    search_fields = ("enrollment__course__title", "lesson__title", "enrollment__member__first_name")


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("certificate_number", "enrollment", "issued_at")
    search_fields = ("certificate_number", "enrollment__course__title", "enrollment__member__first_name")


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("course", "order", "question_text", "correct_option")
    list_filter = ("course",)
    search_fields = ("course__title", "question_text")


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "score", "total_questions", "passed", "attempted_at")
    list_filter = ("passed", "enrollment__course")
    search_fields = ("enrollment__member__first_name", "enrollment__course__title")


@admin.register(WorkshopAttendance)
class WorkshopAttendanceAdmin(admin.ModelAdmin):
    list_display = ("schedule", "enrollment", "status", "marked_at", "marked_by")
    list_filter = ("status", "schedule__course")
    search_fields = ("schedule__title", "enrollment__member__first_name", "enrollment__member__last_name")
