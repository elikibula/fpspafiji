from django.contrib import admin
from django.urls import path, include
from mainapp import views
from reps.views import district_representatives
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path('', views.home, name="home"),
    path('', include('mainapp.urls')),
    path('areas/', include('reps.urls')),
    path('district-representatives/', district_representatives, name='district_representatives'),
    path('training/', include('training.urls')),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('resources/', views.resources, name='resources'),
    path('contact/', views.contact, name='contact'),
   
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



