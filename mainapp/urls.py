from django.contrib import admin
from django.urls import path, include
from mainapp import views
from helpdesk import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('news/', include('news.urls')),
    path('events/', include('events.urls')),
    path('areas/', include('reps.urls')),
    path('membership/', include('membership.urls')),
    path('staff/', include('staff_members.urls')),
    path('helpdesk/', include('helpdesk.urls')),
    path('accounts/', include('accounts.urls')),
    path('documents/', include('documents.urls', namespace='documents')),
    path("faq_list/", views.faq_list, name="faq_list"),        # named 'helpdesk:faq_list'  

]
