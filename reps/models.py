from django.db import models

class Area(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    summary = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

class Branch(models.Model):
    area = models.ForeignKey(Area, related_name='branches', on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=15, decimal_places=9, null=True, blank=True)
    longitude = models.DecimalField(max_digits=15, decimal_places=9, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.area.name})"

class Representative(models.Model):
    area = models.ForeignKey(Area, related_name='reps', on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, related_name='reps', null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=80, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    photo = models.ImageField(upload_to='reps/', null=True, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name
