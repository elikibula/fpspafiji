# staff_members/admin.py
from django.contrib import admin
from .models import StaffMember

@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'position', 'user', 'order', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'user__username', 'user__first_name', 'user__last_name', 'position', 'bio']
    list_editable = ['order', 'is_active']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = []
    
    fieldsets = (
        ('User Link', {
            'fields': ('user',),
            'description': 'Link to an existing website user (optional)'
        }),
        ('Basic Information', {
            'fields': ('name', 'position', 'bio', 'order', 'is_active')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone'),
            'classes': ('collapse',)
        }),
        ('Photo', {
            'fields': ('photo',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def display_name(self, obj):
        return obj.display_name
    display_name.short_description = 'Name'