from django.urls import path

from . import views

app_name = "training"

urlpatterns = [
    path("", views.course_catalog, name="course_catalog"),
    path("my-learning/", views.my_learning, name="my_learning"),
    path("staff/", views.staff_dashboard, name="staff_dashboard"),
    path("staff/courses/", views.staff_course_list, name="staff_course_list"),
    path("staff/courses/create/", views.staff_course_create, name="staff_course_create"),
    path("staff/courses/<int:course_id>/", views.staff_course_detail, name="staff_course_detail"),
    path("staff/courses/<int:course_id>/edit/", views.staff_course_edit, name="staff_course_edit"),
    path("staff/modules/<int:module_id>/edit/", views.staff_module_edit, name="staff_module_edit"),
    path("staff/modules/<int:module_id>/delete/", views.staff_module_delete, name="staff_module_delete"),
    path("staff/lessons/<int:lesson_id>/edit/", views.staff_lesson_edit, name="staff_lesson_edit"),
    path("staff/lessons/<int:lesson_id>/delete/", views.staff_lesson_delete, name="staff_lesson_delete"),
    path("staff/schedules/<int:schedule_id>/edit/", views.staff_schedule_edit, name="staff_schedule_edit"),
    path("staff/schedules/<int:schedule_id>/delete/", views.staff_schedule_delete, name="staff_schedule_delete"),
    path("staff/schedules/<int:schedule_id>/attendance/", views.staff_schedule_attendance, name="staff_schedule_attendance"),
    path("staff/schedules/<int:schedule_id>/qr-poster/", views.staff_schedule_qr_poster, name="staff_schedule_qr_poster"),
    path("staff/quiz-questions/<int:question_id>/edit/", views.staff_quiz_question_edit, name="staff_quiz_question_edit"),
    path("staff/quiz-questions/<int:question_id>/delete/", views.staff_quiz_question_delete, name="staff_quiz_question_delete"),
    path("course/<slug:slug>/", views.course_detail, name="course_detail"),
    path("course/<slug:slug>/enroll/", views.enroll_in_course, name="enroll_in_course"),
    path("learning/<int:enrollment_id>/", views.learning_detail, name="learning_detail"),
    path(
        "learning/<int:enrollment_id>/lesson/<int:lesson_id>/complete/",
        views.mark_lesson_complete,
        name="mark_lesson_complete",
    ),
    path("learning/<int:enrollment_id>/quiz/submit/", views.submit_quiz, name="submit_quiz"),
    path("certificate/<int:certificate_id>/", views.certificate_detail, name="certificate_detail"),
    path("certificate/<int:certificate_id>/print/", views.certificate_print, name="certificate_print"),
    path(
        "attendance/check-in/<int:schedule_id>/<uuid:token>/",
        views.attendance_checkin,
        name="attendance_checkin",
    ),
]
