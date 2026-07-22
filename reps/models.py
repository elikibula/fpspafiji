from django.db import models


class District(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    summary = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class DistrictRepresentative(models.Model):
    district = models.ForeignKey(District, related_name="representatives", on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    role = models.CharField(max_length=100, default="District Representative", blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    photo = models.ImageField(upload_to="reps/district-representatives/", null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["district__name", "order", "name"]

    def __str__(self):
        return f"{self.name} - {self.district.name}"
