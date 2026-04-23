from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'news'

urlpatterns = [
    path('', views.news_list, name='news_list'),
    path('admin/', views.news_admin_list, name='news_admin_list'),  # ⬅ move this up
    path('create/', views.create_news, name='create_news'),
    path('<slug:slug>/edit/', views.update_news, name='update_news'),
    path('<slug:slug>/delete/', views.delete_news, name='delete_news'),
    path('category/<int:pk>/<slug:slug>/', views.category_view, name='category_view'),
    path('news/create/photo/', views.create_photo_news, name='create_photo_news'),
    path('news/photo/<int:pk>/', views.photo_news_detail, name='photo_news_detail'),
    path('photo-news/<int:pk>/update/', views.create_photo_news, name='photo_news_update'),
    path('photo-news/<int:pk>/delete/', views.photo_news_delete, name='photo_news_delete'),
    path('gallery/', views.photo_news_list, name='photo_news_list'),
    path('<int:pk>/', views.news_detail, name='news_detail_by_pk'),
    path('dashboard/', views.news_dashboard, name='news_dashboard'),
    path('analytics/', views.news_analytics, name='news_analytics'),
    path('<slug:slug>/', views.news_detail, name='news_detail'),  # ⬅ keep this last
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
