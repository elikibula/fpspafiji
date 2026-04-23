from django.db import models
from django.urls import reverse
from django.contrib.auth.models import Group
from django.utils import timezone
from django.conf import settings


class DocumentCategory(models.Model):
    name = models.CharField(max_length=200)
    groups = models.ManyToManyField(Group)
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='child_categories')
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('documents:category_detail', kwargs={'pk': self.pk})


class SubCategory(models.Model):
    name = models.CharField(max_length=200)
    groups = models.ManyToManyField(Group)
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.CASCADE,
        related_name='subcategories'
    )

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    def get_absolute_url(self):
        return reverse('documents:subcategory_detail', kwargs={'pk': self.pk})


class Document(models.Model):
    title = models.CharField(max_length=600)
    file = models.FileField(upload_to='documents/')
    description = models.TextField(blank=True)
    category = models.ForeignKey(DocumentCategory, on_delete=models.SET_NULL, null=True)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True)
    date_posted = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='document_author')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='document_owner', null=True)
    groups = models.ManyToManyField(Group)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('documents:document_detail', kwargs={'pk': self.pk})

