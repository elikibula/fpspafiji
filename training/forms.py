from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from .models import Course, CourseSchedule, Lesson, Module, QuizQuestion


RICH_TEXT_CLASS = "django_ckeditor_5 w-full rounded-xl border border-slate-300"


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            "title",
            "short_description",
            "description",
            "learning_outcomes",
            "target_audience",
            "duration_hours",
            "delivery_type",
            "passing_score",
            "thumbnail",
            "is_published",
            "is_featured",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3"}),
            "short_description": forms.TextInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3"}),
            "description": CKEditor5Widget(config_name="default", attrs={"class": RICH_TEXT_CLASS}),
            "learning_outcomes": CKEditor5Widget(config_name="default", attrs={"class": RICH_TEXT_CLASS}),
            "target_audience": forms.TextInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3"}),
            "duration_hours": forms.NumberInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3", "min": 1}),
            "delivery_type": forms.Select(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3"}),
            "passing_score": forms.NumberInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3", "min": 1}),
            "thumbnail": forms.ClearableFileInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3 bg-white"}),
            "is_published": forms.CheckboxInput(attrs={"class": "h-5 w-5 rounded border-slate-300"}),
            "is_featured": forms.CheckboxInput(attrs={"class": "h-5 w-5 rounded border-slate-300"}),
        }


class CourseScheduleForm(forms.ModelForm):
    class Meta:
        model = CourseSchedule
        exclude = ["course", "attendance_qr_token"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3"}),
            "location": forms.TextInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3"}),
            "meeting_link": forms.URLInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3"}),
            "facilitator": forms.TextInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3"}),
            "start_datetime": forms.DateTimeInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3", "type": "datetime-local"}),
            "end_datetime": forms.DateTimeInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3", "type": "datetime-local"}),
            "registration_deadline": forms.DateTimeInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3", "type": "datetime-local"}),
            "capacity": forms.NumberInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3", "min": 1}),
            "notes": forms.Textarea(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3", "rows": 3}),
            "is_active": forms.CheckboxInput(attrs={"class": "h-5 w-5 rounded border-slate-300"}),
            "qr_checkin_enabled": forms.CheckboxInput(attrs={"class": "h-5 w-5 rounded border-slate-300"}),
        }


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        exclude = ["course"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3"}),
            "overview": CKEditor5Widget(config_name="default", attrs={"class": RICH_TEXT_CLASS}),
            "order": forms.NumberInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3", "min": 1}),
        }


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        exclude = ["module"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3"}),
            "content": CKEditor5Widget(config_name="default", attrs={"class": RICH_TEXT_CLASS}),
            "resource_file": forms.ClearableFileInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3 bg-white"}),
            "video_url": forms.URLInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3"}),
            "duration_minutes": forms.NumberInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3", "min": 1}),
            "order": forms.NumberInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3", "min": 1}),
            "is_preview": forms.CheckboxInput(attrs={"class": "h-5 w-5 rounded border-slate-300"}),
        }


class QuizQuestionForm(forms.ModelForm):
    class Meta:
        model = QuizQuestion
        exclude = ["course"]
        widgets = {
            "question_text": forms.Textarea(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3", "rows": 3}),
            "option_a": forms.TextInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3"}),
            "option_b": forms.TextInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3"}),
            "option_c": forms.TextInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3"}),
            "option_d": forms.TextInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3"}),
            "correct_option": forms.Select(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3"}),
            "explanation": CKEditor5Widget(config_name="basic", attrs={"class": RICH_TEXT_CLASS}),
            "order": forms.NumberInput(attrs={"class": "w-full rounded-xl border border-slate-300 px-4 py-3", "min": 1}),
        }
