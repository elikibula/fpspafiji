from django.shortcuts import render
from itertools import chain
from datetime import date
from news.models import News, PhotoNews
from events.models import Event
from django.utils import timezone
from reps.models import Area, Branch
from django.core.serializers import serialize
import json
from decimal import Decimal
from staff_members.models import StaffMember
from helpdesk.models import FAQCategory, FAQ
from django.db.models import Prefetch
from documents.models import DocumentCategory

def home(request):
    # Featured items
    featured_news = (
        News.objects.filter(is_featured=True)
        .select_related('author', 'category')
        .order_by('-date_posted')[:3]
    )
    featured_photo_news = PhotoNews.objects.filter(featured=True).order_by('-date_posted')[:3]

    # Recent news (combine articles and photo news)
    article_news = News.objects.all().order_by('-date_posted')[:10]
    photo_news = PhotoNews.objects.all().order_by('-date_posted')[:10]
    combined_recent_news = list(chain(article_news, photo_news))
    combined_recent_news.sort(key=lambda x: x.date_posted, reverse=True)
    recent_news = combined_recent_news[:6]

    # Upcoming events (future events only)
    upcoming_events = Event.objects.filter(start__gte=timezone.now()).order_by('start')[:6]

    # Areas and Branches (for “Where are we?” section)
    areas = Area.objects.prefetch_related('branches', 'reps').all().order_by('name')
    branches = Branch.objects.prefetch_related('reps', 'area').all()

    # Prepare JSON data for JavaScript map support
    branches_data = []
    for branch in branches:
        branches_data.append({
            'id': branch.id,
            'name': branch.name,
            'address': branch.address,
            'lat': float(branch.latitude) if branch.latitude is not None else None,
            'lng': float(branch.longitude) if branch.longitude is not None else None,
            'area_id': branch.area.id if branch.area else None,
            'reps': [
                {
                    'name': rep.name,
                    'role': rep.role,
                    'phone': rep.phone,
                    'email': rep.email,
                }
                for rep in branch.reps.all()
            ],
        })

    context = {
        'featured_news': featured_news,
        'featured_photo_news': featured_photo_news,
        'latest_news': recent_news,
        'events': upcoming_events,
        'areas': areas,
        'branches_json': json.dumps(branches_data),
    }

    return render(request, "home.html", context)


def about(request):
    # Get active staff members ordered by display order
    staff_members = StaffMember.objects.filter(is_active=True).order_by('order', 'id')
    
    context = {
        'staff_members': staff_members,
        'page_title': 'About FPSPA - Fijian Teachers Association',
        'page_description': 'Learn about FPSPA\'s mission, vision, history, and meet our leadership team serving educators across Fiji since 1934.',
    }
    return render(request, 'about.html', context)


def services(request):
    # Get all active categories, ordered
    faq_categories = FAQCategory.objects.filter(is_active=True).order_by('order', 'name')

    # Prepare FAQs for each category
    for cat in faq_categories:
        # Get active FAQs, ordered
        faqs = FAQ.objects.filter(category=cat, is_active=True).order_by('order', 'question')
        
        # Remove duplicates by question text
        seen = set()
        unique_faqs = []
        for f in faqs:
            if f.question not in seen:
                unique_faqs.append(f)
                seen.add(f.question)
        
        # Attach to category for template
        cat.active_faqs = unique_faqs

    context = {
        'faq_categories': faq_categories,
        'page_title': 'Our Services - FPSPA',
        'page_description': 'Learn about the services offered by the Fijian Teachers Association, including membership, welfare, and FAQs.'
    }
    
    return render(request, 'services.html', context)

def resources(request):
    # Get the Downloads category only
    downloads_category = DocumentCategory.objects.filter(name__iexact="Downloads").first()
    documents = downloads_category.document_set.all() if downloads_category else None
    
    context = {
        "downloads_category": downloads_category,
        "documents": documents,
    }
    return render(request, "resources.html", context)


def contact(request):
    return render(request, 'contact.html')
