from django.contrib.auth.models import User
from django.db.models import Count, Case, When, Avg, F
from django.test import TestCase

from store.models import Book, UserBookRelation
from store.serializers import BooksSerializer


class BookSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user', first_name='Sergey', last_name='Ivanov')
        self.user2 = User.objects.create_user(username='test_user2', first_name='Petr', last_name='Sidorov')
        self.user3 = User.objects.create_user(username='test_user3', first_name='Anton', last_name='Gudimov')

        self.book_1 = Book.objects.create(name='Test book 1', price=25,
                                          author_name='Author 1', owner=self.user)
        self.book_2 = Book.objects.create(name='Test book 2', price=55,
                                          author_name='Author 3', owner=self.user)

    def test_ok(self):
        UserBookRelation.objects.create(user=self.user, book=self.book_1, like=True, rate=5)
        UserBookRelation.objects.create(user=self.user2, book=self.book_1, like=True, rate=4)
        UserBookRelation.objects.create(user=self.user3, book=self.book_1, like=True, rate=5)

        UserBookRelation.objects.create(user=self.user, book=self.book_2, like=True, rate=2)
        UserBookRelation.objects.create(user=self.user2, book=self.book_2, like=True, rate=3)
        UserBookRelation.objects.create(user=self.user3, book=self.book_2, like=False)

        books = Book.objects.all().annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username'),
        ).order_by('id')
        data = BooksSerializer(books, many=True).data
        expected_data = [
            {
                'id': self.book_1.id,
                'name': 'Test book 1',
                'price': '25.00',
                'author_name': 'Author 1',
                # 'likes_count': 3,
                'annotated_likes': 3,
                'rating': '4.67',
                'owner_name': self.user.username,
                'readers': [
                    {
                        'first_name': 'Sergey',
                        'last_name': 'Ivanov'
                    },
                    {
                        'first_name': 'Petr',
                        'last_name': 'Sidorov'
                    },
                    {
                        'first_name': 'Anton',
                        'last_name': 'Gudimov'
                    }
                ]
            },
            {
                'id': self.book_2.id,
                'name': 'Test book 2',
                'price': '55.00',
                'author_name': 'Author 3',
                # 'likes_count': 2,
                'annotated_likes': 2,
                'rating': '2.50',
                'owner_name': self.user.username,
                'readers': [
                    {
                        'first_name': 'Sergey',
                        'last_name': 'Ivanov'
                    },
                    {
                        'first_name': 'Petr',
                        'last_name': 'Sidorov'
                    },
                    {
                        'first_name': 'Anton',
                        'last_name': 'Gudimov'
                    }
                ]
            }
        ]
        print(expected_data, sep='\n\n')
        print(data, sep='\n\n')
        self.assertEqual(expected_data, data)
