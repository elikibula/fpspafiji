from itertools import chain
from django.db.models import Prefetch, Q
from django.db.utils import OperationalError, ProgrammingError
from django.shortcuts import render
from django.utils import timezone

from documents.models import Document, DocumentCategory
from events.models import Event
from helpdesk.models import FAQCategory, FAQ
from news.models import News, PhotoNews
from reps.models import District, DistrictRepresentative
from staff_members.models import StaffMember
from livestream.models import LiveStream


def _safe_list(queryset):
    try: return list(queryset)
    except (OperationalError, ProgrammingError): return []

def _safe_first(queryset):
    try: return queryset.first()
    except (OperationalError, ProgrammingError): return None

def home(request):
    live_stream = _safe_first(
        LiveStream.objects.filter(is_published=True, is_featured=True).order_by(
            '-is_live', '-event_date', '-created_at'
        )
    )
    featured_news = _safe_list(News.objects.filter(is_featured=True).select_related('author', 'category').order_by('-date_posted')[:3])
    featured_photo_news = _safe_list(PhotoNews.objects.filter(featured=True).order_by('-date_posted')[:3])
    combined = _safe_list(News.objects.all().order_by('-date_posted')[:10]) + _safe_list(PhotoNews.objects.all().order_by('-date_posted')[:10])
    combined.sort(key=lambda item: item.date_posted, reverse=True)
    representatives = DistrictRepresentative.objects.filter(is_active=True).order_by('order', 'name')
    districts = _safe_list(District.objects.filter(is_active=True).prefetch_related(Prefetch('representatives', queryset=representatives, to_attr='active_representatives')).order_by('order', 'name'))
    return render(request, 'home.html', {'featured_news': featured_news, 'featured_photo_news': featured_photo_news, 'latest_news': combined[:6], 'events': _safe_list(Event.objects.filter(start__gte=timezone.now()).order_by('start')[:6]), 'areas': districts, 'districts': districts, 'live_stream': live_stream})

def about(request):
    return render(request, 'about.html', {'staff_members': _safe_list(StaffMember.objects.filter(is_active=True).order_by('order', 'id')), 'page_title': 'About FHTA - Fiji Head Teachers Association', 'page_description': 'Learn about FHTA history, mission, functions, and leadership support for primary school head teachers across Fiji.'})

def services(request):
    categories = _safe_list(FAQCategory.objects.filter(is_active=True).order_by('order', 'name'))
    for category in categories:
        seen = set(); category.active_faqs = []
        for faq in _safe_list(FAQ.objects.filter(category=category, is_active=True).order_by('order', 'question')):
            if faq.question not in seen: category.active_faqs.append(faq); seen.add(faq.question)
    return render(request, 'services.html', {'faq_categories': categories, 'page_title': 'Our Services - FHTA', 'page_description': 'Learn about FHTA services, advocacy, professional development, leadership practice, member support, and FAQs.'})

def resources(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()

    public_categories = DocumentCategory.objects.filter(is_public=True).order_by('name')
    documents = Document.objects.filter(category__is_public=True).select_related(
        'category', 'subcategory'
    ).order_by('category__name', 'subcategory__name', '-date_posted', 'title')

    if category_id.isdigit():
        documents = documents.filter(category_id=category_id)
    if query:
        documents = documents.filter(Q(title__icontains=query) | Q(description__icontains=query))

    return render(request, 'resources.html', {
        'public_categories': _safe_list(public_categories),
        'public_documents': _safe_list(documents),
        'selected_category_id': category_id,
        'query': query,
    })

def contact(request): return render(request, 'contact.html')
