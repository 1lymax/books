from django.db.models import Avg



def set_rating(book):
    from store.models import UserBookRelation
    rating = UserBookRelation.objects.filter(book=book).aggregate(rating=Avg('rate')).get('rating')
    book.rating = rating
    book.save()