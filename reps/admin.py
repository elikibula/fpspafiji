# reps/admin.py
from django.contrib import admin
from .models import Area, Branch, Representative
from django.utils.html import format_html

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'area', 'address']
    list_filter = ['area']

@admin.register(Representative)
class RepresentativeAdmin(admin.ModelAdmin):
    list_display = ('photo_tag', 'get_name', 'email', 'phone', 'area', 'branch', 'role')
    list_filter = ('area', 'branch', 'role')
    search_fields = ('name', 'email', 'phone')

    def get_name(self, obj):
        return obj.name or "No Name"
    get_name.short_description = "Name"

    def photo_tag(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="50" height="50" style="object-fit:cover; border-radius:50%;" />', obj.photo.url)
        return "-"
    photo_tag.short_description = "Photo"


