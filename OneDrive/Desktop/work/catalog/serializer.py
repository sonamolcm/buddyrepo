from rest_framework import serializers
from .models import Book


class BookSerializer(serializers.ModelSerializer):

    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'author',
            'description',
            'published_date',
            'isbn',
            'is_available',
            'created_at',
            'updated_at',
        ]