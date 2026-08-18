from django import forms
from .models import Document, SubCategory, DocumentCategory
from tinymce.widgets import TinyMCE


class DocumentCategoryForm(forms.ModelForm):
    class Meta:
        model = DocumentCategory
        fields = ['name', 'groups']  # include fields you want to edit




class DocumentForm(forms.ModelForm):
    MAX_FILE_SIZE = 80 * 1024 * 1024
    description = forms.CharField(widget=TinyMCE(attrs={'cols': 80, 'rows': 10}))

    class Meta:
        model = Document
        fields = ['title', 'file', 'description', 'category', 'subcategory', 'groups']
        widgets = {
            'groups': forms.CheckboxSelectMultiple(),
            'subcategory': forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = "Select a category"
        # Public documents may be filed directly in their public folder.
        # Conditional validation in clean() keeps subcategories required elsewhere.
        self.fields['subcategory'].required = False
        self.fields['subcategory'].queryset = SubCategory.objects.none()

        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = SubCategory.objects.filter(category_id=category_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.category:
            self.fields['subcategory'].queryset = SubCategory.objects.filter(category=self.instance.category)

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        subcategory = cleaned_data.get('subcategory')

        if category and not category.is_public and not subcategory:
            self.add_error('subcategory', 'Please select a subcategory for this category.')
        elif category and subcategory and subcategory.category_id != category.pk:
            self.add_error('subcategory', 'The selected subcategory does not belong to this category.')

        return cleaned_data

    def clean_file(self):
        uploaded_file = self.cleaned_data.get('file')
        if uploaded_file and uploaded_file.size > self.MAX_FILE_SIZE:
            raise forms.ValidationError('File is too large. The maximum upload size is 80 MB.')
        return uploaded_file
