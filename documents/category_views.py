from django.views.generic import DetailView
from .models import DocumentCategory

class CategoryDetail(DetailView):
    model = DocumentCategory
    template_name = 'category_detail.html'
    context_object_name = 'category'