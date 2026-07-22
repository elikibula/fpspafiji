from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('staff', 'National Staff'),
        ('district_staff', 'District Staff'),
        ('member', 'Member'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    phone_number = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Additional fields for staff
    department = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)
    assigned_district = models.ForeignKey(
        'reps.District', null=True, blank=True, related_name='staff_members', on_delete=models.SET_NULL
    )
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def clean(self):
        super().clean()
        if self.role == 'district_staff' and not self.assigned_district_id:
            raise ValidationError({'assigned_district': 'District staff must be assigned to one district.'})
        if self.role != 'district_staff':
            self.assigned_district = None
    
    @property
    def is_staff_user(self):
        return self.role in ['admin', 'staff']
    
    @property
    def is_member_user(self):
        return self.role == 'member'
    
    @property
    def is_admin_user(self):
        return self.role == 'admin'
    
  
