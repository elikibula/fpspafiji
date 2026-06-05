from django.urls import path, include
from helpdesk import views as helpdesk_views

urlpatterns = [
    path('news/', include('news.urls')),
    path('events/', include('events.urls')),
    path('membership/', include('membership.urls')),
    path('staff/', include('staff_members.urls')),
    path('helpdesk/', include('helpdesk.urls')),
    path('accounts/', include('accounts.urls')),
    path('documents/', include('documents.urls', namespace='documents')),
    path("faq_list/", helpdesk_views.faq_list, name="faq_list"),

]
