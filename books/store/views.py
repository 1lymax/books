from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from store.models import Book, UserBookRelation
from store.permissions import IsOwnerOrStaffOrReadOnly
from store.serializers import BooksSerializer, UserBookRelationSerializer


class BookViewSet(ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BooksSerializer
    permission_classes = [IsOwnerOrStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filter_fields = ['price']
    search_fields = ['name', 'author_name']
    ordering_fields = ['price', 'author_name']

    def perform_create(self, serializer):
        serializer.validated_data['owner'] = self.request.user

        serializer.save()


'''
    def filter_queryset(self, request):
        predicate = self.request.query_params  # or request.data for POST
        queryset = self.queryset
        print(queryset, sep='\n')
        if predicate.get('min_price', None) is not None and predicate.get('max_price', None) is not None:
            queryset = self.queryset.filter(price__range=(predicate['min_price'], predicate['max_price']))
            print(1, sep='\n')
        if predicate.get('min_price', None) is not None and predicate.get('max_price', None) is None:
            queryset = self.queryset.filter(price__gte=predicate['min_price'])
            print(2, sep='\n')
        if predicate.get('max_price', None) is not None and predicate.get('min_price', None) is None:
            queryset = self.queryset.filter(price__lte=predicate['max_price'])
            print(3, sep='\n')
        print(queryset, sep='\n')
        return queryset
'''


class UserBookRelationViewSet(UpdateModelMixin, GenericViewSet):
    queryset = UserBookRelation.objects.all()
    serializer_class = UserBookRelationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'book'

    def get_object(self):
        obj, _ = UserBookRelation.objects.get_or_create(user=self.request.user, book_id=self.kwargs['book'])
        return obj



def auth(request):
    return render(request, 'oauth.html')
