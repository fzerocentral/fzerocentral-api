from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework_json_api.pagination import JsonApiPageNumberPagination

from core.utils import filter_queryset_by_param
from .models import Post
from .serializers import PostSerializer


class PostPagination(JsonApiPageNumberPagination):
    # Default page size
    page_size = 20


class PostIndex(ListAPIView):
    serializer_class = PostSerializer
    pagination_class = PostPagination

    def get_queryset(self):
        queryset = Post.objects.all()

        queryset = filter_queryset_by_param(
            self.request, 'topic_id', queryset, 'topic')

        queryset = filter_queryset_by_param(
            self.request, 'before_post_id', queryset, 'id__lt')

        queryset = queryset.order_by('id')
        return queryset


class PostDetail(RetrieveAPIView):
    serializer_class = PostSerializer
    lookup_url_kwarg = 'post_id'

    def get_queryset(self):
        return Post.objects.all()
