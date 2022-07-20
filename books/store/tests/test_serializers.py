from django.contrib.auth.models import User
from django.test import TestCase

from store.models import Book
from store.serializers import BooksSerializer


class BookSerializerTestCase(TestCase):
    def test_ok(self):
        test_user = User.objects.create_user(username='test_user')

        book_1 = Book.objects.create(name='Test book 1', price=25,
                                     author_name='Author 1', owner=test_user)
        book_2 = Book.objects.create(name='Test book 2', price=55,
                                     author_name='Author 3', owner=test_user)
        data = BooksSerializer([book_1, book_2], many=True).data
        expected_data = [
            {
                'id': book_1.id,
                'name': 'Test book 1',
                'price' : '25.00',
                'author_name': 'Author 1',
                'owner': 1
            },
            {
                'id': book_2.id,
                'name': 'Test book 2',
                'price' : '55.00',
                'author_name': 'Author 3',
                'owner': 1
            }
        ]

        self.assertEqual(expected_data, data)