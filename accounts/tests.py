from django.core import mail
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    REGISTRATION_NOTIFICATION_EMAILS=["staff@example.com"],
)
class RegistrationNotificationTests(TestCase):
    def test_registration_sends_staff_notification_email(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("register"),
                {
                    "username": "newmember",
                    "email": "newmember@example.com",
                    "first_name": "New",
                    "last_name": "Member",
                    "password1": "StrongPass123!",
                    "password2": "StrongPass123!",
                },
            )

        self.assertRedirects(response, reverse("complete_member_profile"))
        self.assertEqual(len(mail.outbox), 1)

        notification = mail.outbox[0]
        self.assertEqual(notification.to, ["staff@example.com"])
        self.assertIn("New FPSPA user registered", notification.subject)
        self.assertIn("Username: newmember", notification.body)
        self.assertIn("Email: newmember@example.com", notification.body)

    def test_staff_dashboard_shows_recent_registration_notification(self):
        User = get_user_model()
        staff = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="StrongPass123!",
            first_name="Staff",
            last_name="User",
            role="staff",
        )
        User.objects.create_user(
            username="freshmember",
            email="freshmember@example.com",
            password="StrongPass123!",
            first_name="Fresh",
            last_name="Member",
        )

        self.client.force_login(staff)
        response = self.client.get(reverse("staff_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Registration Notification")
        self.assertContains(response, "freshmember@example.com")
