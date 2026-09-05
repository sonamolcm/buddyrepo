from django.http import request
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Book
from .forms import BookForm
from .serializer import BookSerializer

class BookListCreateAPIView(APIView):

    def get(self, request):
        search = request.GET.get('search')

        if search:
            books = Book.objects.filter(
                title__icontains=search
            ) | Book.objects.filter(
                author__icontains=search
            )
        else:
            books = Book.objects.all()

        serializer = BookSerializer(books, many=True)

        return Response(serializer.data)

    def post(self, request):
        serializer = BookSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)

    return render(
        request,
        'book_detail.html',
        {'book': book}
    )
class BookDetailAPIView(APIView):

    def get_book(self, pk):
        return get_object_or_404(Book, pk=pk)

    def get(self, request, pk):
        book = self.get_book(pk)
        serializer = BookSerializer(book)
        return Response(serializer.data)

    def put(self, request, pk):
        book = self.get_book(pk)
        serializer = BookSerializer(book, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, pk):
        book = self.get_book(pk)
        serializer = BookSerializer(
            book,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk):
        book = self.get_book(pk)
        book.delete()

        return Response(
            {"message": "Book deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )

def book_create(request):

    if request.method == 'POST':
        form = BookForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Book created successfully!')
            return redirect('book_create')

    else:
        form = BookForm()

    return render(
        request,
        'book_form.html',
        {'form': form}
    )

def book_update(request, pk):

    book = get_object_or_404(Book, pk=pk)

    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)

        if form.is_valid():
            form.save()
            messages.success(request, 'Book updated successfully!')
            return redirect('book_update', pk=book.pk)

    else:
        form = BookForm(instance=book)

    return render(
        request,
        'book_form.html',
        {
            'form': form,
            'book': book
        }
    )


def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)

    if request.method == 'POST':
        book.deleted_at = timezone.now()
        book.save()

        messages.success(request, 'Book moved to trash.')
        return redirect('book_list')

    return render(
        request,
        'bookconfirmdelete.html',
        {'book': book}
    )

def trash(request):
    books = Book.objects.filter(deleted_at__isnull=False)

    return render(
        request,
        'trash.html',
        {'books': books}
    )
def book_restore(request, pk):

    book = get_object_or_404(Book, pk=pk)

    if request.method == 'POST':
        book.deleted_at = None
        book.save()

        messages.success(request, 'Book restored successfully.')
        return redirect('trash')

    return redirect('trash')

def book_list(request):
    books = Book.objects.filter(deleted_at__isnull=True)

    return render(
        request,
        'book_list.html',
        {'books': books}
    )