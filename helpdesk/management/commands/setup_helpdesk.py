# helpdesk/management/commands/setup_helpdesk.py
from django.core.management.base import BaseCommand
from helpdesk.models import TicketStream, TicketStatus, TicketPriority, TicketCategory

class Command(BaseCommand):
    help = 'Setup initial helpdesk data'

    def handle(self, *args, **options):
        # Create ticket streams
        streams = [
            ('member', 'Member Support', 'Member-submitted tickets'),
            ('staff', 'Staff Internal', 'Staff-created tickets for internal issues'),
            ('reception', 'Reception', 'Walk-in and phone support tickets'),
        ]
        
        for slug, name, desc in streams:
            stream, created = TicketStream.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'description': desc}
            )
            if created:
                self.stdout.write(f'✓ Created stream: {name}')

        # Create ticket statuses
        statuses = [
            ('Open', '#EF4444', False),
            ('In Progress', '#F59E0B', False),
            ('Waiting for Customer', '#8B5CF6', False),
            ('Resolved', '#10B981', True),
            ('Closed', '#6B7280', True),
        ]
        
        for name, color, is_resolved in statuses:
            status, created = TicketStatus.objects.get_or_create(
                name=name,
                defaults={'color': color, 'is_resolved': is_resolved}
            )
            if created:
                self.stdout.write(f'✓ Created status: {name}')

        # Create ticket priorities
        priorities = [
            ('Low', '#10B981', 1),
            ('Medium', '#F59E0B', 2),
            ('High', '#EF4444', 3),
            ('Urgent', '#DC2626', 4),
        ]
        
        for name, color, order in priorities:
            priority, created = TicketPriority.objects.get_or_create(
                name=name,
                defaults={'color': color, 'order': order}
            )
            if created:
                self.stdout.write(f'✓ Created priority: {name}')

        # Create some default categories
        categories = [
            ('Technical Support', 'Computer, software, and technical issues', 1),
            ('Membership', 'Membership registration and inquiries', 2),
            ('Payments', 'Payment and billing issues', 3),
            ('Training', 'Training and professional development', 4),
            ('General Inquiry', 'General questions and information', 5),
        ]
        
        for name, description, order in categories:
            category, created = TicketCategory.objects.get_or_create(
                name=name,
                defaults={'description': description, 'order': order}
            )
            if created:
                self.stdout.write(f'✓ Created category: {name}')

        self.stdout.write(self.style.SUCCESS('✓ Successfully setup helpdesk data!'))