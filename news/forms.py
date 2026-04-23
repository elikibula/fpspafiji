from django import forms
from .models import PhotoNews, News, Category, Comment
from tinymce.widgets import TinyMCE

# ✅ Custom widget that supports multiple file uploads
from django.forms.widgets import ClearableFileInput
from django_ckeditor_5.widgets import CKEditor5Widget

class NewsForm(forms.ModelForm):
    content = forms.CharField(
        widget=CKEditor5Widget(config_name='default', attrs={
            'class': 'django_ckeditor_5 ckeditor-content w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-fta-gold focus:border-fta-gold',
            'placeholder': 'Write your article content here...'
        })
    )

    class Meta:
        model = News
        # Exclude fields that should be auto-set or system-managed
        exclude = ['author', 'slug', 'date_posted', 'updated_at']

        # Add styling to other fields
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-fta-gold focus:border-fta-gold',
                'placeholder': 'Enter the article title'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-fta-gold focus:border-fta-gold'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 bg-gray-50 cursor-pointer focus:ring-2 focus:ring-fta-gold',
                'multiple': False  # set True if you allow multiple images
            }),
        }
class MultiFileInput(ClearableFileInput):
    allow_multiple_selected = True

from django import forms
from .models import PhotoNews

class PhotoNewsForm(forms.ModelForm):
    class Meta:
        model = PhotoNews
        fields = ['title', 'category', 'description', 'cover_image', 'image']
        widgets = {
            'description': forms.Textarea(attrs={
                'placeholder': 'Enter a detailed description...',
                'class': 'w-full rounded-xl border border-gray-300 px-4 py-3 focus:ring-2 focus:ring-maroon-600 focus:border-maroon-600 shadow-sm h-48 resize-none',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.visible_fields():
            if field.name != 'description':
                field.field.widget.attrs.update({
                    'class': 'w-full rounded-xl border border-gray-300 px-4 py-2.5 focus:ring-2 focus:ring-maroon-600 focus:border-maroon-600 shadow-sm'
                })
        # Allow multiple file uploads for the image field
        self.fields['image'].widget.attrs.update({
            'multiple': True,
            'accept': 'image/*'
        })


# ✅ Comment Form
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
