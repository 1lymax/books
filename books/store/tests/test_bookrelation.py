from django.contrib.auth.models import User
from django.test import TestCase

from store.bookrelation import set_rating
from store.models import Book, UserBookRelation


class bookrelationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user', first_name='Sergey', last_name='Ivanov')
        self.user2 = User.objects.create_user(username='test_user2', first_name='Petr', last_name='Sidorov')
        self.user3 = User.objects.create_user(username='test_user3', first_name='Anton', last_name='Gudimov')

        self.book = Book.objects.create(name='Test book 1', price=25,
                                          author_name='Author 1', owner=self.user)

        UserBookRelation.objects.create(user=self.user, book=self.book, like=True, rate=5)
        UserBookRelation.objects.create(user=self.user2, book=self.book, like=True, rate=4)
        UserBookRelation.objects.create(user=self.user3, book=self.book, like=True, rate=5)

    def test_set_rating(self):
        set_rating(self.book)
        self.book.refresh_from_db()
        self.assertEqual(4.67, float(self.book.rating))
