from django import forms
from .models import Book


class BookForm(forms.ModelForm):

    class Meta:
        model = Book
        fields = [
            'title',
            'author',
            'description',
            'published_date',
            'isbn',
            'is_available',
        ]

        labels = {
            'title': 'Book Title',
            'author': 'Author Name',
            'description': 'Book Description',
            'published_date': 'Published Date',
            'isbn': 'ISBN Number',
            'is_available': 'Available',
        }

    def clean_title(self):
        title = self.cleaned_data['title']

        if len(title) < 3:
            raise forms.ValidationError(
                'Title must contain at least 3 characters.'
            )

        return title

    def clean_author(self):
        author = self.cleaned_data['author']

        if len(author) < 3:
            raise forms.ValidationError(
                'Author name must contain at least 3 characters.'
            )

        return author

    def clean_isbn(self):
        isbn = self.cleaned_data['isbn']

        if len(isbn) != 13:
            raise forms.ValidationError(
                'ISBN must contain exactly 13 characters.'
            )

        if not isbn.isdigit():
            raise forms.ValidationError(
                'ISBN must contain only numbers.'
            )

        return isbn