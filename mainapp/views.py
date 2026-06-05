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
from django.db.utils import OperationalError, ProgrammingError
from documents.models import DocumentCategory


DISTRICT_DISTRIBUTION = [
    ("suva", "Suva", 80),
    ("nausori", "Nausori", 119),
    ("nadi", "Nadi", 33),
    ("nadroga-navosa", "Nadroga/Navosa", 63),
    ("lautoka-yasawa", "Lautoka/Yasawa", 52),
    ("ba", "Ba", 43),
    ("tavua-vatukoula-nadarivatu", "Tavua/Vatukoula/Nadarivatu", 19),
    ("rakiraki", "Rakiraki", 43),
    ("macuata", "Macuata", 71),
    ("bua", "Bua", 29),
    ("cakaudrove", "Cakaudrove", 66),
    ("eastern", "Eastern", 117),
]


class _EmptyRelation:
    def all(self):
        return []


class DistrictArea:
    branches = _EmptyRelation()
    reps = _EmptyRelation()

    def __init__(self, slug, name, hos_count):
        self.id = slug
        self.slug = slug
        self.name = name
        self.hos_count = hos_count
        self.summary = f"{hos_count} Heads of Schools recorded in the current FPSPA district distribution."


def _district_areas():
    return [DistrictArea(slug, name, hos_count) for slug, name, hos_count in DISTRICT_DISTRIBUTION]


def _safe_list(queryset):
    try:
        return list(queryset)
    except (OperationalError, ProgrammingError):
        return []


def _safe_first(queryset):
    try:
        return queryset.first()
    except (OperationalError, ProgrammingError):
        return None


def home(request):
    # Featured items
    featured_news = _safe_list(
        News.objects.filter(is_featured=True)
        .select_related('author', 'category')
        .order_by('-date_posted')[:3]
    )
    featured_photo_news = _safe_list(PhotoNews.objects.filter(featured=True).order_by('-date_posted')[:3])

    # Recent news (combine articles and photo news)
    article_news = _safe_list(News.objects.all().order_by('-date_posted')[:10])
    photo_news = _safe_list(PhotoNews.objects.all().order_by('-date_posted')[:10])
    combined_recent_news = list(chain(article_news, photo_news))
    combined_recent_news.sort(key=lambda x: x.date_posted, reverse=True)
    recent_news = combined_recent_news[:6]

    # Upcoming events (future events only)
    upcoming_events = _safe_list(Event.objects.filter(start__gte=timezone.now()).order_by('start')[:6])

    # Areas and Branches (for “Where are we?” section)
    areas = _district_areas()
    branches = []

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
    try:
        staff_members = list(StaffMember.objects.filter(is_active=True).order_by('order', 'id'))
    except (OperationalError, ProgrammingError):
        staff_members = []
    
    context = {
        'staff_members': staff_members,
        'page_title': 'About FPSPA - Fiji Primary School Principals Association',
        'page_description': 'Learn about FPSPA history, mission, functions, and leadership support for primary school principals across Fiji.',
    }
    return render(request, 'about.html', context)


def services(request):
    # Get all active categories, ordered
    faq_categories = _safe_list(FAQCategory.objects.filter(is_active=True).order_by('order', 'name'))

    # Prepare FAQs for each category
    for cat in faq_categories:
        # Get active FAQs, ordered
        faqs = _safe_list(FAQ.objects.filter(category=cat, is_active=True).order_by('order', 'question'))
        
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
        'page_description': 'Learn about FPSPA services, advocacy, professional development, leadership practice, member support, and FAQs.'
    }
    
    return render(request, 'services.html', context)

def resources(request):
    # Get the Downloads category only
    downloads_category = _safe_first(DocumentCategory.objects.filter(name__iexact="Downloads"))
    documents = _safe_list(downloads_category.document_set.all()) if downloads_category else None
    
    context = {
        "downloads_category": downloads_category,
        "documents": documents,
    }
    return render(request, "resources.html", context)


def contact(request):
    return render(request, 'contact.html')
