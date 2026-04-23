# helpdesk/admin.py
from django.contrib import admin
from .models import *

@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active']
    list_editable = ['order', 'is_active']

@admin.register(TicketPriority)
class TicketPriorityAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'order']
    list_editable = ['color', 'order']

@admin.register(TicketStatus)
class TicketStatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'is_resolved']

class TicketResponseInline(admin.TabularInline):
    model = TicketResponse
    extra = 1
    readonly_fields = ['created_at']

@admin.register(HelpdeskTicket)
class HelpdeskTicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'title', 'category', 'priority', 'status', 'created_by', 'created_at']
    list_filter = ['category', 'priority', 'status', 'created_at']
    search_fields = ['ticket_number', 'title', 'description']
    readonly_fields = ['ticket_number', 'created_at', 'updated_at']
    inlines = [TicketResponseInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'priority', 'status', 'created_by')

@admin.register(FAQCategory)
class FAQCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active']
    list_editable = ['order', 'is_active']

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'order', 'is_active']
    list_filter = ['category', 'is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['question', 'answer']