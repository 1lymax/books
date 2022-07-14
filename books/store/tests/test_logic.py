from django.test import TestCase

from store.logic import operation
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "books.settings")

class LogicTestCase(TestCase):
    def test_plus(self):
        result = operation (6, 13, '+')
        self.assertEqual(19, result)

    def test_minus(self):
        result = operation (6, 13, '-')
        self.assertEqual(-7, result)

    def test_multiply(self):
        result = operation (6, 13, '*')
        self.assertEqual(78, result)