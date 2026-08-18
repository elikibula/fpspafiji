from django.contrib import admin

from .models import LiveStream


@admin.register(LiveStream)
class LiveStreamAdmin(admin.ModelAdmin):
    list_display = ('title', 'platform', 'event_date', 'is_live', 'is_featured', 'is_published', 'updated_at')
    list_filter = ('platform', 'is_live', 'is_featured', 'is_published', 'event_date')
    search_fields = ('title', 'description', 'stream_url')
    readonly_fields = ('platform', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('title', 'description', 'stream_url', 'platform')}),
        ('Event status', {'fields': ('event_date', 'is_live', 'is_featured', 'is_published')}),
        ('Presentation', {'fields': ('thumbnail',)}),
        ('Audit', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
