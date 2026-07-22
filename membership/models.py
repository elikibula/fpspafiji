from django.conf import settings
from django.db import models
from datetime import date


def current_year():
    return date.today().year


class MemberCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class School(models.Model):
    name = models.CharField(max_length=300)
    district = models.ForeignKey('reps.District', on_delete=models.CASCADE)
    school_type = models.ForeignKey(MemberCategory, on_delete=models.CASCADE)
    address = models.TextField()
    
    def __str__(self):
        return self.name

class Member(models.Model):
    MEMBERSHIP_STATUS = [
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('inactive', 'Inactive'),
        ('returned', 'Returned for correction'),
        ('rejected', 'Rejected'),
    ]
  
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name="member_profile")
    membership_number = models.CharField(max_length=20, unique=True, blank=True)
    
    # Personal details
    first_name = models.CharField(max_length=100,null=True)
    last_name = models.CharField(max_length=100, null=True)
    dob = models.DateField("Date of birth", null=True, blank=True)
    tpf_number = models.CharField(max_length=20, null=True)    
    ftra_register_num = models.CharField("FTRA registration number", max_length=50, null=True, blank=True, db_index=True)
    email = models.EmailField(null=True)
    phone_number = models.CharField(max_length=20, null=True)
    residing_address = models.TextField(null=True)
    
    # Professional details
    category = models.ForeignKey(MemberCategory, on_delete=models.CASCADE,null=True)
    district = models.ForeignKey('reps.District', on_delete=models.PROTECT, null=True, blank=True, related_name='members')
    school = models.CharField(max_length=300, blank=True, null=True)
    position = models.CharField(max_length=200, null=True)
    start_year = models.IntegerField(default=current_year)
    
    # Membership details
    membership_status = models.CharField(max_length=20, choices=MEMBERSHIP_STATUS, default='pending')
    date_joined = models.DateTimeField(auto_now_add=True)
    
    # Additional information
    profile_photo = models.ImageField(upload_to='member_photos/', null=True, blank=True)
    id_document = models.FileField(upload_to='member_documents/', null=True, blank=True)
    
    class Meta:
        ordering = ['tpf_number']
    
    def save(self, *args, **kwargs):
        if not self.membership_number:
            year = date.today().year
            last_member = Member.objects.order_by('id').last()
            if last_member:
                new_id = last_member.id + 1
            else:
                new_id = 1
            self.membership_number = f"FTA{year}{new_id:06d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.tpf_number} - {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    @property
    def age(self):
        if not self.dob:
            return None
        today = date.today()
        return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))

    @property
    def age_display(self):
        return f"{self.age} years" if self.age is not None else "Not provided"
    
    @property
    def years_of_service(self):
        if self.start_year:
            current_year = date.today().year
            return current_year - self.start_year
        return 0

    @property
    def years_as_principal(self):
        return self.years_of_service
    
    @property
    def years_of_service_display(self):
        years = self.years_of_service
        if years == 0:
            return "First year"
        elif years == 1:
            return "1 year"
        else:
            return f"{years} years"

    @property
    def years_as_principal_display(self):
        return self.years_of_service_display


class MembershipApprovalAudit(models.Model):
    ACTIONS = [('approved', 'Approved'), ('returned', 'Returned'), ('rejected', 'Rejected')]
    application = models.ForeignKey(Member, related_name='approval_audits', on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTIONS)
    acting_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='membership_actions', on_delete=models.PROTECT)
    staff_district = models.ForeignKey('reps.District', null=True, blank=True, on_delete=models.PROTECT)
    previous_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    comment = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
