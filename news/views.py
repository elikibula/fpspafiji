from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import News, Category, PhotoNews, PhotoNewsImage
from .forms import NewsForm, PhotoNewsForm
from itertools import chain
from operator import attrgetter
from django.db.models import Count
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.text import slugify
import uuid
from django.db.models import Q




@login_required
def create_news(request):
    form = NewsForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        news = form.save(commit=False)
        news.author = request.user
        news.save()
        return redirect('news:news_detail', slug=news.slug)
    return render(request, 'news/create_news.html', {'form': form})


@login_required
def update_news(request, slug):
    news = get_object_or_404(News, slug=slug)
    form = NewsForm(request.POST or None, request.FILES or None, instance=news)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('news:news_admin_list')  # ← Fix is here
    return render(request, 'news/news_form.html', {'form': form})



@login_required
def delete_news(request, pk=None, slug=None):
    if pk:
        news = get_object_or_404(News, pk=pk)
    elif slug:
        news = get_object_or_404(News, slug=slug)
    else:
        messages.error(request, "No news identifier provided.")
        return redirect('news_list')  # or some fallback page

    if request.method == 'POST':
        news.delete()
        messages.success(request, "News deleted successfully.")
        return redirect('news_list')

    return render(request, 'news/delete_news.html', {'news': news})


def news_detail(request, slug):
    news = get_object_or_404(News, slug=slug)
    recent_news = News.objects.exclude(pk=news.pk).order_by('-date_posted')[:5]
    categories = Category.objects.all()
    for cat in categories:
        cat.total_count = News.objects.filter(category=cat).count() + PhotoNews.objects.filter(category=cat).count()
    return render(request, 'news/news_detail.html', {
        'news': news,
        'recent_news': recent_news,
        'categories': categories,
    })

def category_news(request, slug):
    category = get_object_or_404(Category, slug=slug)
    news_list = News.objects.filter(category=category).order_by('-date_posted')
    photo_news_list = PhotoNews.objects.filter(category=category).order_by('-date_posted')
    combined_news = list(chain(news_list, photo_news_list))
    combined_news.sort(key=lambda x: x.date_posted, reverse=True)
    
    return render(request, 'news/category_news.html', {
        'category': category,
        'news_list': combined_news,
    })

# ----------------------
# PHOTO NEWS VIEWS
# ----------------------
@login_required
def create_photo_news(request):
    form = PhotoNewsForm(request.POST or None, request.FILES or None)
    image_filename = None

    # Show uploaded filename if form fails validation
    if request.method == 'POST' and request.FILES.get('cover_image'):
        image_filename = request.FILES['cover_image'].name

    if request.method == 'POST' and form.is_valid():
        photo_news = form.save(commit=False)
        photo_news.author = request.user

        # Assign cover image explicitly
        cover = request.FILES.get('cover_image')
        if cover:
            photo_news.cover_image = cover

        photo_news.save()

        # Save multiple gallery images
        images = request.FILES.getlist('image')
        for img in images[:20]:  # Limit to 20 images
            PhotoNewsImage.objects.create(photonews=photo_news, image=img)

        return redirect('news:photo_news_detail', pk=photo_news.pk)

    return render(request, 'news/create_photo_news.html', {
        'form': form,
        'image_filename': image_filename,
    })



@login_required
def photo_news_update(request, pk):
    photo_news = get_object_or_404(PhotoNews, pk=pk)
    form = PhotoNewsForm(request.POST or None, request.FILES or None, instance=photo_news)

    # compute filename from existing instance (if present)
    image_filename = None
    if getattr(photo_news, 'cover_image', None):
        # safe split for unix/win paths
        image_filename = photo_news.cover_image.name.split('/')[-1].split('\\')[-1]

    if request.method == 'POST' and form.is_valid():
        # Use commit=False to allow overwriting cover_image if a new one was uploaded
        updated = form.save(commit=False)
        uploaded_cover = request.FILES.get('cover_image')
        if uploaded_cover:
            updated.cover_image = uploaded_cover
            # update image_filename to the newly uploaded one
            image_filename = uploaded_cover.name
        updated.save()

        # (optional) handle gallery images on update if provided
        images = request.FILES.getlist('images')
        for img in images[:20]:
            PhotoNewsImage.objects.create(photonews=updated, image=img)

        return redirect('news:news_admin_list')

    return render(request, 'news/photo_news_form.html', {
        'form': form,
        'photo_news': photo_news,
        'image_filename': image_filename,
    })


# ----------------------
# PHOTO NEWS DETAIL VIEWS
# ----------------------
def photo_news_detail(request, pk):
    """
    Ensure we always pass: photo_news, categories, recent_news
    and provide safe fallbacks for description and preview image fields.
    """
    # load photo news instance (try PhotoNews first, fall back to News)
    try:
        photo_news = get_object_or_404(PhotoNews, pk=pk)
    except Exception:
        photo_news = get_object_or_404(News, pk=pk)

    # prepare description fallback
    description = getattr(photo_news, 'description', None) or getattr(photo_news, 'content', '') or getattr(photo_news, 'caption', '')

    # categories with a total_count annotation (adjust relation if needed)
    # If Category has a m2m or FK to News/PhotoNews named 'news', change accordingly.
    categories = Category.objects.annotate(total_count=Count('news')).order_by('-total_count')[:20]

    # recent news: combine latest News and PhotoNews (customize per your models)
    recent_news = list(News.objects.order_by('-date_posted')[:6])
    # optionally include PhotoNews in recent list if separate model:
    try:
        recent_news += list(PhotoNews.objects.order_by('-date_uploaded')[:4])
    except Exception:
        pass
    # dedupe & limit
    # ensure each item has preview image attribute named 'image' (or fallback)
    seen = set()
    deduped = []
    for item in recent_news:
        if getattr(item, 'pk', None) in seen:
            continue
        seen.add(item.pk)
        # add a safe `image` property if not present
        if not hasattr(item, 'image') or not getattr(item, 'image', None):
            # fallback field names
            item.image = getattr(item, 'cover_image', None) or getattr(item, 'thumbnail', None) or None
        deduped.append(item)
        if len(deduped) >= 6:
            break

    context = {
        'photo_news': photo_news,
        'description': description,
        'categories': categories,
        'recent_news': deduped,
    }
    return render(request, 'news/photo_news_detail.html', context)




# ----------------------
# COMBINED NEWS LIST
# ----------------------

def news_list(request):
    # fetch items
    articles = News.objects.all()
    photos = PhotoNews.objects.all()

    # Combine and sort all news by date (newest first)
    news_posts = sorted(
        chain(articles, photos),
        key=lambda x: x.date_posted,
        reverse=True
    )

    # categories with totals
    categories = Category.objects.all()
    for category in categories:
        category.news_count = News.objects.filter(category=category).count()
        category.photo_count = PhotoNews.objects.filter(category=category).count()
        category.total_count = category.news_count + category.photo_count

    # Pagination
    per_page = 12  # change this value to show more/less per page
    paginator = Paginator(news_posts, per_page)
    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        # page_obj is the paginated page; it is iterable
        'page_obj': page_obj,
        # convenience alias for template compatibility (if you prefer to use news_list)
        'news_list': page_obj.object_list,
        'categories': categories,
    }
    return render(request, 'news/news.html', context)
# ----------------------
# CATEGORY FILTER VIEW
# ----------------------

def category_view(request, pk, slug):
    # Get the current category or return 404
    category = get_object_or_404(Category, pk=pk, slug=slug)

    # Fetch all news and photo news under this category
    articles = News.objects.filter(category=category).order_by('-date_posted')
    galleries = PhotoNews.objects.filter(category=category).order_by('-date_posted')

    # Fetch recent news not from this category for suggestions or sidebar
    recent_news = News.objects.exclude(category=category).order_by('-date_posted')[:5]

    # Fetch all categories and annotate with total news/photo count
    categories = Category.objects.all()
    for cat in categories:
        cat.total_count = (
            News.objects.filter(category=cat).count() +
            PhotoNews.objects.filter(category=cat).count()
        )

    # Render category view
    return render(request, 'news/category.html', {
        'category': category,
        'articles': articles,
        'galleries': galleries,
        'recent_news': recent_news,
        'categories': categories,
    })


@login_required
def news_admin_list(request):
    # Query both models
    news_qs = News.objects.all().select_related('category', 'author')
    photo_qs = PhotoNews.objects.all().select_related('category', 'author')

    # Combine into a single list
    combined = list(chain(news_qs, photo_qs))

    # Attach a safe attribute for template use
    for obj in combined:
        obj.model_name = obj.__class__.__name__.lower()  # e.g. 'news' or 'photonews'

    # Sort by date_posted (fallback to date_uploaded)
    def _get_date(o):
        return getattr(o, 'date_posted', None) or getattr(o, 'date_uploaded', None)

    combined_sorted = sorted(combined, key=_get_date, reverse=True)

    # Paginate
    page_number = request.GET.get('page', 1)
    paginator = Paginator(combined_sorted, 12)
    page_obj = paginator.get_page(page_number)

    return render(request, 'news/news_list.html', {
        'page_obj': page_obj,
    })

@login_required
def photo_news_list(request):
    photos = PhotoNews.objects.all().order_by('-date_posted')
    return render(request, 'news/photo_news_list.html', {
        'photo_posts': photos
    })



@login_required
def photo_news_delete(request, pk):
    photo_news = get_object_or_404(PhotoNews, pk=pk)
    if request.method == 'POST':
        photo_news.delete()
        messages.success(request, "Photo news deleted successfully.")
        return redirect('news:news_admin_list')
    return render(request, 'news/photo_news_confirm_delete.html', {'photo_news': photo_news})

def save(self, *args, **kwargs):
    if not self.slug:
        self.slug = slugify(self.title)
        while News.objects.filter(slug=self.slug).exists():
            self.slug = f"{slugify(self.title)}-{str(uuid.uuid4())[:4]}"
    super().save(*args, **kwargs)

@login_required
def news_dashboard(request):
    """Main dashboard for news management - Working version"""
    if request.user.role not in ['admin', 'staff']:
        messages.error(request, 'Access denied.')
        return redirect('member_dashboard')
    
    # Basic statistics
    total_news = News.objects.count()
    total_photo_news = PhotoNews.objects.count()
    total_categories = Category.objects.count()
    
    # Recent activity (last 7 days)
    one_week_ago = timezone.now() - timedelta(days=7)
    recent_news = News.objects.filter(date_posted__gte=one_week_ago).count()
    recent_photo_news = PhotoNews.objects.filter(date_posted__gte=one_week_ago).count()
    
    # Category statistics
    categories = Category.objects.all()
    category_stats = []
    
    for category in categories:
        news_count = News.objects.filter(category=category).count()
        photo_count = PhotoNews.objects.filter(category=category).count()
        
        category_stats.append({
            'category': category,
            'news_count': news_count,
            'photo_news_count': photo_count,
            'total_count': news_count + photo_count
        })
    
    # Sort by total count
    category_stats.sort(key=lambda x: x['total_count'], reverse=True)
    
    # Recent content
    latest_news = News.objects.all().order_by('-date_posted')[:5]
    latest_photo_news = PhotoNews.objects.all().order_by('-date_posted')[:5]
    
    # Check if is_featured field exists and count featured articles
    try:
        featured_news = News.objects.filter(is_featured=True).count()
    except:
        featured_news = 0
    
    # Count articles with images
    articles_with_images = News.objects.exclude(image='').count()
    
    context = {
        'total_news': total_news,
        'total_photo_news': total_photo_news,
        'total_categories': total_categories,
        'recent_news': recent_news,
        'recent_photo_news': recent_photo_news,
        'category_stats': category_stats,
        'latest_news': latest_news,
        'latest_photo_news': latest_photo_news,
        'featured_news': featured_news,
        'articles_with_images': articles_with_images,
    }
    return render(request, 'news/dashboard.html', context)

@login_required
def news_analytics(request):
    """Detailed analytics for news content"""
    if request.user.role not in ['admin', 'staff']:
        messages.error(request, 'Access denied.')
        return redirect('member_dashboard')
    
    # Time-based analytics
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    # News posted in last 30 days
    recent_news_trend = News.objects.filter(
        date_posted__date__gte=last_30_days
    ).extra({
        'date': "date(date_posted)"
    }).values('date').annotate(count=Count('id')).order_by('date')
    
    # Category distribution
    categories = Category.objects.all()
    category_stats = []
    
    for category in categories:
        news_count = News.objects.filter(category=category).count()
        photo_count = PhotoNews.objects.filter(category=category).count()
        
        category_stats.append({
            'category': category,
            'news_count': news_count,
            'photo_count': photo_count,
            'total_count': news_count + photo_count
        })
    
    # Sort by total count
    category_stats.sort(key=lambda x: x['total_count'], reverse=True)
    
    # Most active authors
    from django.contrib.auth import get_user_model
    User = get_user_model()
    active_authors = User.objects.annotate(
        news_count=Count('news'),
        photo_news_count=Count('photo_news')
    ).filter(
        Q(news_count__gt=0) | Q(photo_news_count__gt=0)
    ).order_by('-news_count')[:10]
    
    # Content statistics
    total_news = News.objects.count()
    total_photo_news = PhotoNews.objects.count()
    
    # Check if is_featured field exists
    try:
        featured_articles = News.objects.filter(is_featured=True).count()
    except:
        featured_articles = 0
    
    # Articles with images
    articles_with_images = News.objects.exclude(image='').count()
    
    context = {
        'recent_news_trend': list(recent_news_trend),
        'category_stats': category_stats,
        'active_authors': active_authors,
        'last_30_days': last_30_days,
        'total_news': total_news,
        'total_photo_news': total_photo_news,
        'featured_articles': featured_articles,
        'articles_with_images': articles_with_images,
    }
    return render(request, 'news/analytics.html', context)
