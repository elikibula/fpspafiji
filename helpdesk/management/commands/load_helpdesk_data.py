# helpdesk/management/commands/load_helpdesk_data.py
from django.core.management.base import BaseCommand
from helpdesk.models import TicketCategory, TicketPriority, TicketStatus, FAQCategory, FAQ

class Command(BaseCommand):
    help = 'Load initial helpdesk data'

    def handle(self, *args, **options):
        # Ticket Statuses
        statuses = [
            {'name': 'Open', 'color': '#10B981', 'is_resolved': False},
            {'name': 'In Progress', 'color': '#F59E0B', 'is_resolved': False},
            {'name': 'Resolved', 'color': '#6B7280', 'is_resolved': True},
            {'name': 'Closed', 'color': '#EF4444', 'is_resolved': True},
        ]
        
        for status_data in statuses:
            TicketStatus.objects.get_or_create(**status_data)
        
        # Ticket Priorities
        priorities = [
            {'name': 'Low', 'color': '#6B7280', 'order': 1},
            {'name': 'Medium', 'color': '#F59E0B', 'order': 2},
            {'name': 'High', 'color': '#EF4444', 'order': 3},
            {'name': 'Urgent', 'color': '#DC2626', 'order': 4},
        ]
        
        for priority_data in priorities:
            TicketPriority.objects.get_or_create(**priority_data)
        
        # Ticket Categories
        categories = [
            {'name': 'Membership', 'description': 'Membership registration, renewal, and account issues'},
            {'name': 'Technical Support', 'description': 'Website, login, and technical issues'},
            {'name': 'Payments & Fees', 'description': 'Payment processing and fee-related questions'},
            {'name': 'Events & Training', 'description': 'Workshops, events, and professional development'},
            {'name': 'General Inquiry', 'description': 'General questions and information requests'},
        ]
        
        for i, category_data in enumerate(categories):
            category_data['order'] = i + 1
            TicketCategory.objects.get_or_create(**category_data)
        
        self.stdout.write(self.style.SUCCESS('Successfully loaded helpdesk initial data'))



