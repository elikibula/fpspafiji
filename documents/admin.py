from django.contrib import admin
from .models import Document, DocumentCategory, SubCategory


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'get_subcategory']
    exclude = ('author', 'owner', 'date_posted')  # ✅ Hides them from the admin form
    filter_horizontal = ('groups',)

    def get_subcategory(self, obj):
        return obj.subcategory.name if obj.subcategory else "-"
    get_subcategory.short_description = 'Subcategory'

    def save_model(self, request, obj, form, change):
        # ✅ Set both fields to the current user
        if not obj.pk:
            obj.author = request.user
            obj.owner = request.user
        super().save_model(request, obj, form, change)


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent_category']
    filter_horizontal = ('groups',)


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):    
    list_display = ['name', 'category']
    search_fields = ['name']
    filter_horizontal = ('groups',)
