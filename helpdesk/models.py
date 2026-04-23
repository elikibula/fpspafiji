# helpdesk/models.py
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
User = get_user_model()

class TicketCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = 'Ticket Categories'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name

class TicketPriority(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#6B7280')  # Hex color
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name_plural = 'Ticket Priorities'
        ordering = ['order']
    
    def __str__(self):
        return self.name

class TicketStatus(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#6B7280')
    is_resolved = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name


class FAQCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = 'FAQ Categories'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name

class FAQ(models.Model):
    question = models.CharField(max_length=200)
    answer = models.TextField()
    category = models.ForeignKey(FAQCategory, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category__order', 'order', 'question']
    
    def __str__(self):
        return self.question
    
class TicketStream(models.Model):
    """Represents different ticket streams (Member, Staff, etc.)"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class HelpdeskTicket(models.Model):
    ticket_number = models.CharField(max_length=20, unique=True, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(TicketCategory, on_delete=models.PROTECT, null=True, blank=True)
    priority = models.ForeignKey(TicketPriority, on_delete=models.PROTECT, null=True, blank=True)
    status = models.ForeignKey(TicketStatus, on_delete=models.PROTECT, null=True, blank=True)
    
    # User information
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_tickets')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    
    # Stream / source
    stream = models.ForeignKey(TicketStream, on_delete=models.PROTECT, null=True, blank=True)
    source = models.CharField(max_length=50, choices=[
        ('web', 'Web Portal'),
        ('email', 'Email'),
        ('phone', 'Phone Call'),
        ('walkin', 'Walk-in'),
        ('internal', 'Internal'),
    ], default='web')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # SLA fields
    due_date = models.DateTimeField(null=True, blank=True)
    first_response_at = models.DateTimeField(null=True, blank=True)
    resolution_due_at = models.DateTimeField(null=True, blank=True)
    
    # Additional fields
    attachment = models.FileField(upload_to='ticket_attachments/', null=True, blank=True)
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.ticket_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = self.generate_ticket_number()
        
        # Set due dates based on priority and stream if not already set
        if not self.due_date:
            self.set_due_dates()
            
        super().save(*args, **kwargs)
    
    def generate_ticket_number(self):
        import uuid
        return f"FTA-{uuid.uuid4().hex[:8].upper()}"
    
    def set_due_dates(self):
        """Set SLA due dates based on priority and stream"""
        from datetime import timedelta
        
        # Base SLA hours based on priority name
        sla_hours = {
            'High': 4,    # High priority - 4 hours
            'Medium': 24,  # Medium priority - 24 hours  
            'Low': 72,     # Low priority - 72 hours
        }
        
        priority_name = getattr(self.priority, 'name', 'Medium')
        hours = sla_hours.get(priority_name, 24)
        
        self.due_date = timezone.now() + timedelta(hours=hours)
        self.resolution_due_at = timezone.now() + timedelta(hours=hours * 2)
    
    def get_absolute_url(self):
        return reverse('helpdesk:ticket_detail', kwargs={'ticket_number': self.ticket_number})
    
    @property
    def is_resolved(self):
        return bool(self.status and getattr(self.status, 'is_resolved', False))
    
    @property
    def days_open(self):
        return (timezone.now() - self.created_at).days if self.created_at else None
    
    @property
    def is_overdue(self):
        if self.due_date and not self.first_response_at:
            return timezone.now() > self.due_date
        return False
    
    @property
    def is_resolution_overdue(self):
        if self.resolution_due_at and not self.is_resolved:
            return timezone.now() > self.resolution_due_at
        return False


class TicketResponse(models.Model):
    ticket = models.ForeignKey(HelpdeskTicket, on_delete=models.CASCADE, related_name='responses')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    attachment = models.FileField(upload_to='response_attachments/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_internal_note = models.BooleanField(default=False)
    
    # Visibility / response type
    VISIBILITY_CHOICES = [
        ('public', 'Visible to Member'),
        ('internal', 'Internal Staff Only'),
        ('hidden', 'Hidden from Member'),
    ]
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    
    RESPONSE_TYPE_CHOICES = [
        ('reply', 'Reply'),
        ('note', 'Internal Note'),
        ('system', 'System Update'),
    ]
    response_type = models.CharField(max_length=20, choices=RESPONSE_TYPE_CHOICES, default='reply')
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Response to {self.ticket.ticket_number if self.ticket else 'Unknown'}"