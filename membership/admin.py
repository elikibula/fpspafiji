from django.contrib import admin
from django.utils.html import format_html
from .models import MemberCategory, School, Member, MembershipApprovalAudit

admin.site.register(MemberCategory)
admin.site.register(School)

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('tpf_number', 'full_name', 'email', 'district', 'membership_status', 'date_joined')
    list_filter = ('membership_status', 'category', 'district')
    search_fields = ('tpf_number', 'first_name', 'last_name', 'email', 'phone_number')
    list_select_related = ('user', 'category', 'district')
    readonly_fields = ('date_joined', 'profile_photo_preview')

    @admin.display(description='Photo')
    def profile_photo_preview(self, obj):
        if obj.profile_photo:
            return format_html('<img src="{}" width="100" height="100" style="object-fit:cover;border-radius:8px">', obj.profile_photo.url)
        return 'No photo'

@admin.register(MembershipApprovalAudit)
class MembershipApprovalAuditAdmin(admin.ModelAdmin):
    list_display = ('application', 'action', 'acting_user', 'staff_district', 'previous_status', 'new_status', 'timestamp')
    list_filter = ('action', 'staff_district', 'timestamp')
    search_fields = ('application__first_name', 'application__last_name', 'acting_user__username', 'comment')
    readonly_fields = ('application', 'action', 'acting_user', 'staff_district', 'previous_status', 'new_status', 'comment', 'timestamp')

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
