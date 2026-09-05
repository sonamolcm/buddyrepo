from django.contrib import admin
from .models import Book
from .forms import BookForm


admin.site.register(Book)