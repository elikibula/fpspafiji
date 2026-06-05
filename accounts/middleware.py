from django.shortcuts import redirect
from django.db.utils import OperationalError, ProgrammingError

from membership.models import Member


class PendingMemberApprovalMiddleware:
    """Keep registered members out of authenticated content until staff approve them."""

    ALLOWED_PREFIXES = (
        "/accounts/complete-profile/",
        "/accounts/pending-approval/",
        "/accounts/logout/",
        "/accounts/login/",
        "/static/",
        "/media/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated and getattr(user, "role", None) == "member":
            path = request.path
            if not any(path.startswith(prefix) for prefix in self.ALLOWED_PREFIXES):
                try:
                    member = Member.objects.get(user=user)
                except Member.DoesNotExist:
                    return redirect("complete_member_profile")
                except (OperationalError, ProgrammingError):
                    return self.get_response(request)

                if member.membership_status != "active":
                    return redirect("pending_approval")

        return self.get_response(request)
