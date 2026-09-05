from django.urls import path
from .views import BookListCreateAPIView, book_create, BookDetailAPIView, book_update, book_delete, trash, book_restore, book_list

urlpatterns = [
    path('books/create/', book_create, name='book_create'),
    path('api/books/', BookListCreateAPIView.as_view(), name='book-list-create'),
    path('api/books/<int:pk>/', BookDetailAPIView.as_view(), name='book-detail'),
    path('books/<int:pk>/edit/', book_update, name='book_update'),
    path('books/trash/', trash, name='trash'),
    path('books/<int:pk>/delete/', book_delete, name='book_delete'),
    
    path( 'books/<int:pk>/restore/',book_restore,name='book_restore'),
    path( 'books/',book_list,name='book_list' ),
]


