# membership/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import MemberCategory, School, Member

@admin.register(MemberCategory)
class MemberCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'member_count']
    search_fields = ['name']
    list_per_page = 20
    
    def member_count(self, obj):
        return obj.member_set.count()
    member_count.short_description = 'Total Members'

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'area', 'school_type', 'address_preview']
    list_filter = ['area', 'school_type']
    search_fields = ['name', 'address']
    list_select_related = ['area', 'school_type']
    list_per_page = 25
    
    def address_preview(self, obj):
        return obj.address[:50] + '...' if len(obj.address) > 50 else obj.address
    address_preview.short_description = 'Address'

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = [
        'tpf_number', 'full_name', 'email', 'category', 
        'area', 'years_of_service_display_admin', 
        'membership_status', 'date_joined'
    ]
    list_filter = [
        'membership_status', 'category', 'area',  
        'start_year', 'date_joined'
    ]
    search_fields = [
        'tpf_number', 'first_name', 'last_name', 'email', 
        'phone_number', 'position'
    ]
    readonly_fields = [
        'date_joined', 'years_of_service_display_admin',
        'profile_photo_preview'
    ]
    list_select_related = ['user', 'category', 'area','school']
    list_per_page = 50
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'tpf_number', 'first_name', 'last_name', 'email', 
                'phone_number', 'profile_photo', 'profile_photo_preview'
            )
        }),
        ('Professional Details', {
            'fields': (
                'category', 'area', 'school', 'position', 
                'start_year', 'years_of_service_display_admin'
            )
        }),
        ('Membership Information', {
            'fields': (
                'membership_status', 'date_joined', 'id_document'
            )
        }),
        ('User Account', {
            'fields': ('user',),
            'classes': ('collapse',)
        }),
    )
    
    def years_of_service_display_admin(self, obj):
        years = obj.years_of_service
        if years == 0:
            return format_html('<span style="color: green;">First year</span>')
        elif years == 1:
            return format_html('<span style="color: blue;">1 year</span>')
        else:
            color = 'blue' if years < 5 else 'orange' if years < 20 else 'red'
            return format_html(f'<span style="color: {color};">{years} years</span>')
    years_of_service_display_admin.short_description = 'Years of Service'
    
    def profile_photo_preview(self, obj):
        if obj.profile_photo:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover; border-radius: 8px;" />',
                obj.profile_photo.url
            )
        return "No photo"
    profile_photo_preview.short_description = 'Profile Photo Preview'
    
    # Bulk actions
    actions = ['approve_members', 'suspend_members', 'deactivate_members']
    
    def approve_members(self, request, queryset):
        updated = queryset.update(membership_status='active')
        self.message_user(request, f'{updated} members approved successfully.')
    approve_members.short_description = "Approve selected members"
    
    def suspend_members(self, request, queryset):
        updated = queryset.update(membership_status='suspended')
        self.message_user(request, f'{updated} members suspended.')
    suspend_members.short_description = "Suspend selected members"
    
    def deactivate_members(self, request, queryset):
        updated = queryset.update(membership_status='inactive')
        self.message_user(request, f'{updated} members deactivated.')
    deactivate_members.short_description = "Deactivate selected members"