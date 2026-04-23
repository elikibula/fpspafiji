# staff_members/models.py
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User

class StaffMember(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, help_text="Link to an existing website user (optional)")
    name = models.CharField(
        max_length=200,
        help_text="Will auto-fill if user is selected"
    )
    position = models.CharField(
        max_length=100,
        help_text="e.g., President, Vice President, General Secretary, etc."
    )
    bio = models.TextField(blank=True, help_text="Brief biography or description")
    email = models.EmailField(blank=True, help_text="Will auto-fill if user is selected")
    phone = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to='staff_photos/', blank=True, null=True)
    order = models.PositiveIntegerField(
        default=0, 
        help_text="Display order (lower numbers show first)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Staff Member'
        verbose_name_plural = 'Staff Members'
    
    def __str__(self):
        return f"{self.name} - {self.position}"
    
    def get_absolute_url(self):
        return reverse('staff_members:member_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        # Auto-fill name and email from user if user is selected
        if self.user:
            if not self.name:
                self.name = f"{self.user.first_name} {self.user.last_name}".strip()
            if not self.email:
                self.email = self.user.email
        super().save(*args, **kwargs)
    
    @property
    def display_name(self):
        """Returns the name from user or manual entry"""
        if self.user:
            return f"{self.user.first_name} {self.user.last_name}".strip()
        return self.name
    
    @property
    def display_email(self):
        """Returns the email from user or manual entry"""
        if self.user and self.user.email:
            return self.user.email
        return self.email