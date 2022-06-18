from rest_framework.generics import ListAPIView, RetrieveAPIView

from .models import Category
from .serializers import CategorySerializer


class CategoryIndex(ListAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.all().order_by('order')


class CategoryDetail(RetrieveAPIView):
    serializer_class = CategorySerializer
    lookup_url_kwarg = 'category_id'

    def get_queryset(self):
        return Category.objects.all()
