# membership/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Member

@receiver(post_save, sender=User)
def create_member_profile(sender, instance, created, **kwargs):
    """
    Create a Member profile when a new User registers.
    """
    if created:
        try:
            # Generate membership number
            last_member = Member.objects.order_by('id').last()
            if last_member:
                new_id = last_member.id + 1
            else:
                new_id = 1
            membership_number = f"TPF{new_id:06d}"
            
            # Create Member instance with only essential fields
            Member.objects.create(
                user=instance,
                email=instance.email,
                membership_number=membership_number,
                # Other fields will be filled in later via profile completion
            )
        except Exception as e:
            print(f"Error creating member profile: {e}")

@receiver(post_save, sender=User)
def save_member_profile(sender, instance, **kwargs):
    """
    Save Member profile when User is saved.
    """
    try:
        if hasattr(instance, 'member'):
            instance.member.save()
    except Member.DoesNotExist:
        # Member doesn't exist yet, which is fine
        pass