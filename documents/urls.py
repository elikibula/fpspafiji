from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # Main document listing / dashboard
    path('', views.document_list, name='document_list'),

    # Upload
    path('upload/', views.upload_document, name='upload_document'),
 

    path("downloads/", views.public_downloads, name="public_downloads"),

    # Document CRUD & helpers
    path('document/<int:pk>/', views.document_detail, name='document_detail'),
    path('document/<int:pk>/view/', views.view_document, name='document_view'),
    path('document/<int:pk>/inline/', views.inline_document, name='document_inline'),
    path('document/<int:pk>/preview/', views.embedded_preview, name='document_preview'),
    path('document/<int:pk>/download/', views.download_document, name='document_download'),
    path('public/<int:pk>/download/', views.download_public_document, name='public_document_download'),
    path('document/<int:pk>/edit/', views.document_edit, name='document_edit'),
    path('document/<int:pk>/delete/', views.delete_document, name='document_delete'),
    

    # Categories and subcategories
    path('category/<int:pk>/', views.category_detail, name='category_detail'),
    path('subcategory/<int:pk>/', views.subcategory_detail, name='subcategory_detail'),

    # Downloads section
    path('downloads/', views.download_view, name='downloads'),
    path('downloads/subcategory/<int:pk>/', views.download_subcategory_detail, name='download_subcategory_detail'),

    # AJAX endpoints
   path('ajax/subcategories/', views.ajax_subcategories, name='ajax_subcategories'),
    
]
