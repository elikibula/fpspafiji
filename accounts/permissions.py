from django.core.exceptions import PermissionDenied


NATIONAL_ROLES = {'admin', 'staff'}


def get_staff_district(user):
    if not user.is_authenticated or user.role != 'district_staff':
        return None
    return user.assigned_district


def is_national_administrator(user):
    return user.is_authenticated and (user.is_superuser or user.role in NATIONAL_ROLES)


def user_can_manage_application(user, application):
    if is_national_administrator(user):
        return True
    district = get_staff_district(user)
    return district is not None and application.district_id == district.id


def require_application_access(user, application):
    if not user_can_manage_application(user, application):
        raise PermissionDenied('You cannot manage membership applications outside your district.')
