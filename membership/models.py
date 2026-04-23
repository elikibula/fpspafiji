from django.conf import settings
from django.db import models
from datetime import date

class MemberCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class School(models.Model):
    name = models.CharField(max_length=300)
    area = models.ForeignKey('reps.Area', on_delete=models.CASCADE)
    branch = models.ForeignKey('reps.Branch', on_delete=models.CASCADE, related_name='schools')
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
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name="member_profile")
    membership_number = models.CharField(max_length=20, unique=True, blank=True)
    
    # Personal details
    first_name = models.CharField(max_length=100,null=True)
    last_name = models.CharField(max_length=100, null=True)
    tpf_number = models.CharField(max_length=20, null=True)    
    email = models.EmailField(null=True)
    phone_number = models.CharField(max_length=20, null=True)
    residing_address = models.TextField(null=True)
    
    # Professional details
    category = models.ForeignKey(MemberCategory, on_delete=models.CASCADE,null=True)
    area = models.ForeignKey('reps.Area', on_delete=models.CASCADE,null=True)
    branch = models.ForeignKey('reps.Branch', on_delete=models.CASCADE,null=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    position = models.CharField(max_length=200, null=True)
    start_year = models.IntegerField(default=date.today().year)
    
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
        return f"{self.first_name} {self.last_name}"
    
    @property
    def years_of_service(self):
        if self.start_year:
            current_year = date.today().year
            return current_year - self.start_year
        return 0
    
    @property
    def years_of_service_display(self):
        years = self.years_of_service
        if years == 0:
            return "First year"
        elif years == 1:
            return "1 year"
        else:
            return f"{years} years"