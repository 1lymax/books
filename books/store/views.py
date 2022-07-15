from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from store.models import Book
from store.serializers import BooksSerializer


class BookViewSet(ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BooksSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filter_fields = ['price']
    search_fields = ['name', 'author_name']
    ordering_fields = ['price', 'author_name']

    def filter_queryset(self, request):
        predicate = self.request.query_params  # or request.data for POST
        queryset = self.queryset
        if predicate.get('min_price', None) is not None and predicate.get('max_price', None) is not None:
            queryset = self.queryset.filter(price__range=(predicate['min_price'], predicate['max_price']))
        if predicate.get('min_price', None) is not None and predicate.get('max_price', None) is None:
            queryset = self.queryset.filter(price__gte=predicate['min_price'])
        if predicate.get('max_price', None) is not None and predicate.get('min_price', None) is None:
            queryset = self.queryset.filter(price__lte=predicate['max_price'])
        return queryset


def auth(request):
    return render(request, 'oauth.html')