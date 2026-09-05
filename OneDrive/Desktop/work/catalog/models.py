from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=150)
    description = models.TextField()
    published_date = models.DateField()
    isbn = models.CharField(max_length=13, unique=True)
    is_available = models.BooleanField(default=True)

    deleted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)