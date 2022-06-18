from rest_framework.generics import ListAPIView, RetrieveAPIView

from core.utils import filter_queryset_by_param
from .models import Forum
from .serializers import ForumSerializer


class ForumIndex(ListAPIView):
    serializer_class = ForumSerializer

    def get_queryset(self):
        queryset = Forum.objects.all()

        queryset = filter_queryset_by_param(
            self.request, 'category_id', queryset, 'category')

        queryset = queryset.order_by('category__order', 'order')
        return queryset


class ForumDetail(RetrieveAPIView):
    serializer_class = ForumSerializer
    lookup_url_kwarg = 'forum_id'

    def get_queryset(self):
        return Forum.objects.all()
