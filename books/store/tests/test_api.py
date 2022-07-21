import json
import os

from django.contrib.auth.models import User
from django.db import connection
from django.db.models import Count, Case, When, Avg, F
from django.test.utils import CaptureQueriesContext
from rest_framework.exceptions import ErrorDetail

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "books.settings")

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from store.models import Book, UserBookRelation
from store.serializers import BooksSerializer


class BooksApiTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user')
        self.staff_user = User.objects.create_user(username='staff_user', is_staff=True)
        self.book_1 = Book.objects.create(name='Test book 1', price=25,
                                          author_name='Author 1', owner=self.user)
        self.book_2 = Book.objects.create(name='Test book 2', price=55,
                                          author_name='Author 2')
        self.book_3 = Book.objects.create(name='Test book 3 Author 1', price=65,
                                          author_name='Author 1')
        self.book_4 = Book.objects.create(name='Test book 4', price=55,
                                          author_name='Author 3')

        UserBookRelation.objects.create(user=self.user, book=self.book_2, like=True, rate=5)

    def test_get(self):
        url = reverse('book-list')
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)
            self.assertEqual(2, len(queries))
        books = Book.objects.all().annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username')
        ).order_by('id')
        serializer_data = BooksSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)
        self.assertEqual(serializer_data[1]['rating'], '5.00')
        # self.assertEqual(serializer_data[0]['likes_count'], 1)
        self.assertEqual(serializer_data[1]['annotated_likes'], 1)


    def test_get_filter(self):
        url = reverse('book-list')
        books = Book.objects.filter(price=55).annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username')
        )
        response = self.client.get(url, data={'price': 55})
        serializer_data = BooksSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_search(self):
        url = reverse('book-list')
        books = Book.objects.filter(id__in=[self.book_1.id, self.book_3.id]).annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username'),
            # rating=Avg('userbookrelation__rate')
        )
        response = self.client.get(url, data={'search': 'Author 1'})
        serializer_data = BooksSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        # print(serializer_data, sep='\n')
        # print(response.data, sep='\n')
        self.assertEqual(serializer_data, response.data)

    def test_get_ordering_ascending(self):
        url = reverse('book-list')
        books = Book.objects.all().annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username')
        ).order_by('author_name').select_related('owner')
        response = self.client.get(url, data={'ordering': 'author_name'})
        serializer_data = BooksSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_ordering_descending(self):
        url = reverse('book-list')
        books = Book.objects.all().annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username'),
            #rating=Avg('userbookrelation__rate')
        ).select_related('owner').order_by('-author_name')
        response = self.client.get(url, data={'ordering': '-author_name'})
        serializer_data = BooksSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    # def test_get_price_range(self):
    #     url = reverse('book-list')
    #     books = Book.objects.filter(price__gte=20, price__lte=60).annotate(
    #         annotated_likes=Count(Case(When(userbookrelation__like=True, then=1)))
    #     )
    #     response = self.client.get(url, data={'min_price': '20', 'max_price': '60'})
    #     serializer_data = BooksSerializer(books, many=True).data
    #     self.assertEqual(status.HTTP_200_OK, response.status_code)
    #     self.assertEqual(serializer_data, response.data)

    def test_create(self):
        self.assertEqual(4, Book.objects.all().count())
        url = reverse('book-list')
        data = {
            'name': 'Programming in Python 3',
            'price': 150,
            'author_name': 'Mark Summerfield'
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.post(url, data=json_data,
                                    content_type='application/json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(self.user, Book.objects.last().owner)
        self.assertEqual(5, Book.objects.all().count())

    def test_update(self):
        url = reverse('book-detail', args=(self.book_1.id,))
        data = {
            'name': self.book_1.name,
            'price': 500,
            'author_name': self.book_1.author_name
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.put(url, data=json_data,
                                   content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.book_1.refresh_from_db()
        self.assertEqual(500, self.book_1.price)

        # попытка изменения чужой записи

    def test_update_not_owner(self):
        url = reverse('book-detail', args=(self.book_2.id,))
        data = {
            'name': self.book_2.name,
            'price': 500,
            'author_name': self.book_2.author_name
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.put(url, data=json_data,
                                   content_type='application/json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual({'detail': ErrorDetail(string='You do not have permission to perform this action.',
                                                code='permission_denied')}
                         , response.data)
        self.book_2.refresh_from_db()
        self.assertEqual(55, self.book_2.price)

    def test_delete(self):
        self.assertEqual(4, Book.objects.all().count())
        url = reverse('book-detail', args=(self.book_1.id,))

        self.client.force_login(self.user)
        response = self.client.delete(url)
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(3, Book.objects.all().count())

    def test_delete_not_owner(self):
        self.assertEqual(4, Book.objects.all().count())
        url = reverse('book-detail', args=(self.book_2.id,))

        self.client.force_login(self.user)
        response = self.client.delete(url)
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual({'detail': ErrorDetail(string='You do not have permission to perform this action.',
                                                code='permission_denied')}
                         , response.data)
        self.assertEqual(4, Book.objects.all().count())

    def test_update_not_owner_but_staff(self):
        url = reverse('book-detail', args=(self.book_2.id,))
        data = {
            'name': self.book_2.name,
            'price': 500,
            'author_name': self.book_2.author_name
        }
        json_data = json.dumps(data)
        self.client.force_login(self.staff_user)
        response = self.client.put(url, data=json_data,
                                   content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.book_2.refresh_from_db()
        self.assertEqual(500, self.book_2.price)


class UserBookRelationTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user')
        self.user2 = User.objects.create_user(username='test_user2')
        self.staff_user = User.objects.create_user(username='staff_user', is_staff=True)
        self.book_1 = Book.objects.create(name='Test book 1', price=25,
                                          author_name='Author 1', owner=self.user)
        self.book_2 = Book.objects.create(name='Test book 2', price=55,
                                          author_name='Author 2')
        self.book_3 = Book.objects.create(name='Test book 3 Author 1', price=65,
                                          author_name='Author 1')
        self.book_4 = Book.objects.create(name='Test book 4', price=55,
                                          author_name='Author 3')

    def test_like_and_bookmarks(self):
        url = reverse('userbookrelation-detail', args=(self.book_2.id,))
        self.client.force_login(self.user)
        data = {
            'like': True,
        }
        json_data = json.dumps(data)
        response = self.client.patch(url, data=json_data,
                                     content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user, book=self.book_2)
        self.assertTrue(True, relation.like)

        data = {
            'in_bookmarks': True,
        }
        json_data = json.dumps(data)
        response = self.client.patch(url, data=json_data,
                                     content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user, book=self.book_2)
        self.assertTrue(True, relation.in_bookmarks)

    def test_rate(self):
        url = reverse('userbookrelation-detail', args=(self.book_2.id,))
        self.client.force_login(self.user)
        data = {
            'rate': 3,
        }
        json_data = json.dumps(data)
        response = self.client.patch(url, data=json_data,
                                     content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user, book=self.book_2)
        self.assertEqual(3, relation.rate)

    def test_rate_wrong(self):
        url = reverse('userbookrelation-detail', args=(self.book_2.id,))
        self.client.force_login(self.user)
        data = {
            'rate': 6,
        }
        json_data = json.dumps(data)
        response = self.client.patch(url, data=json_data,
                                     content_type='application/json')
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual({'rate': [ErrorDetail(string='"6" is not a valid choice.', code='invalid_choice')]},
                          response.data)
