import logging

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone


logger = logging.getLogger(__name__)


def get_registration_notification_recipients():
    recipients = getattr(settings, "REGISTRATION_NOTIFICATION_EMAILS", [])
    if isinstance(recipients, str):
        recipients = [email.strip() for email in recipients.split(",")]

    recipients = [email for email in recipients if email]
    if recipients:
        return recipients

    contact_email = getattr(settings, "FTA_SETTINGS", {}).get("CONTACT_EMAIL")
    return [contact_email] if contact_email else []


def send_user_registration_notification(user, request=None):
    recipients = get_registration_notification_recipients()
    if not recipients:
        logger.warning("No registration notification recipients configured.")
        return

    registered_at = timezone.localtime(user.date_joined).strftime("%d %b %Y, %I:%M %p")
    staff_dashboard_url = reverse("staff_dashboard")
    if request is not None:
        staff_dashboard_url = request.build_absolute_uri(staff_dashboard_url)

    subject = f"New FPSPA user registered: {user.get_full_name() or user.username}"
    message = "\n".join(
        [
            "A new user has registered on the FPSPA website.",
            "",
            f"Name: {user.get_full_name() or '-'}",
            f"Username: {user.username}",
            f"Email: {user.email or '-'}",
            f"Role: {user.get_role_display()}",
            f"Registered: {registered_at}",
            "",
            f"Staff dashboard: {staff_dashboard_url}",
        ]
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=recipients,
            fail_silently=False,
        )
    except Exception:
        logger.exception("Failed to send registration notification for user %s.", user.pk)
