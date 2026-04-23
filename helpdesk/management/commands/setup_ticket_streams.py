# helpdesk/management/commands/setup_ticket_streams.py
from django.core.management.base import BaseCommand
from helpdesk.models import TicketStream, TicketStatus, TicketPriority

class Command(BaseCommand):
    help = 'Setup initial ticket streams and statuses'

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
                self.stdout.write(f'Created stream: {name}')
        
        # Ensure we have basic statuses
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
                self.stdout.write(f'Created status: {name}')
        
        self.stdout.write(self.style.SUCCESS('Successfully setup ticket streams!'))