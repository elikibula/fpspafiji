# membership/urls.py
from django.urls import path, include
from . import views


app_name = 'membership'

urlpatterns = [

    path('accounts/', include('accounts.urls')),
   

]



   
    
    
    
   
