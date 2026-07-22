from django.core import mail
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from membership.models import Member, MembershipApprovalAudit
from reps.models import District, DistrictRepresentative
from accounts.forms import MemberRegistrationForm


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
        self.assertIn("New FHTA user registered", notification.subject)
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


class DistrictWorkflowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.suva = District.objects.create(name='Suva', slug='suva')
        self.nadi = District.objects.create(name='Nadi', slug='nadi')
        self.staff = User.objects.create_user(username='districtstaff', password='StrongPass123!', role='district_staff', assigned_district=self.suva)
        self.member_user = User.objects.create_user(username='applicant', password='StrongPass123!', role='member')
        self.other_user = User.objects.create_user(username='other', password='StrongPass123!', role='member')
        self.member = Member.objects.create(user=self.member_user, first_name='Suva', last_name='Member', district=self.suva)
        self.other = Member.objects.create(user=self.other_user, first_name='Nadi', last_name='Member', district=self.nadi)
        self.client.force_login(self.staff)

    def test_dashboard_only_contains_assigned_district_members(self):
        response = self.client.get(reverse('staff_dashboard'))
        self.assertContains(response, 'Suva Member')
        self.assertNotContains(response, 'Nadi Member')

    def test_staff_cannot_approve_another_district(self):
        response = self.client.post(reverse('approve_member', args=[self.other.pk]))
        self.assertEqual(response.status_code, 403)
        self.other.refresh_from_db()
        self.assertEqual(self.other.membership_status, 'pending')

    def test_approval_is_atomic_and_audited(self):
        response = self.client.post(reverse('approve_member', args=[self.member.pk]), {'comment': 'Verified'})
        self.assertRedirects(response, reverse('staff_dashboard'))
        audit = MembershipApprovalAudit.objects.get(application=self.member)
        self.assertEqual((audit.action, audit.acting_user, audit.staff_district), ('approved', self.staff, self.suva))

    def test_unassigned_staff_sees_no_members(self):
        self.staff.assigned_district = None
        self.staff.save(update_fields=['assigned_district'])
        response = self.client.get(reverse('staff_dashboard'))
        self.assertContains(response, 'has not been assigned to a district')
        self.assertNotContains(response, 'Suva Member')


class RegistrationDistrictTests(TestCase):
    def test_district_is_required_and_inactive_is_rejected(self):
        inactive = District.objects.create(name='Closed', slug='closed', is_active=False)
        form = MemberRegistrationForm(data={'district': inactive.pk})
        self.assertFalse(form.is_valid())
        self.assertIn('district', form.errors)


class RepresentativeAndPasswordTests(TestCase):
    def test_only_active_representatives_appear(self):
        district = District.objects.create(name='Suva', slug='suva')
        DistrictRepresentative.objects.create(district=district, name='Active Rep', phone='123', email='rep@example.com')
        DistrictRepresentative.objects.create(district=district, name='Hidden Rep', is_active=False)
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Active Rep')
        self.assertNotContains(response, 'Hidden Rep')
        self.assertNotContains(response, 'leaflet', html=False)

    def test_password_change_keeps_user_logged_in(self):
        user = get_user_model().objects.create_user(username='member', password='OldStrong123!', role='member')
        self.client.force_login(user)
        response = self.client.post(reverse('password_change'), {'old_password': 'OldStrong123!', 'new_password1': 'NewStrong456!', 'new_password2': 'NewStrong456!'})
        self.assertRedirects(response, reverse('password_change_done'))
        self.assertIn('_auth_user_id', self.client.session)
