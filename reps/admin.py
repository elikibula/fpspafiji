from django.contrib import admin
from django.utils.html import format_html

from .models import District, DistrictRepresentative


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "summary")
    ordering = ("order", "name")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(DistrictRepresentative)
class DistrictRepresentativeAdmin(admin.ModelAdmin):
    list_display = ("photo_preview", "name", "district", "role", "phone", "email", "order", "is_active")
    list_filter = ("district", "is_active")
    search_fields = ("name", "district__name", "phone", "email")
    ordering = ("district__name", "order", "name")
    list_select_related = ("district",)
    readonly_fields = ("photo_preview",)

    @admin.display(description="Photo")
    def photo_preview(self, obj):
        if obj and obj.photo:
            return format_html('<img src="{}" width="50" height="50" style="object-fit:cover;border-radius:50%">', obj.photo.url)
        return "—"
