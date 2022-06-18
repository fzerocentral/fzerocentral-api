from django.db.models import Max
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework_json_api.pagination import JsonApiPageNumberPagination

from core.utils import filter_queryset_by_param
from .models import Topic
from .serializers import TopicSerializer


class TopicPagination(JsonApiPageNumberPagination):
    # Default page size
    page_size = 50


class TopicIndex(ListAPIView):
    serializer_class = TopicSerializer
    pagination_class = TopicPagination

    def get_queryset(self):
        queryset = Topic.objects.all()

        queryset = filter_queryset_by_param(
            self.request, 'forum_id', queryset, 'forum')

        # Order topics by id of latest post.
        # TODO: Should exclude moved topics, since those don't have posts
        #  directly under them and end up being listed first.
        queryset = queryset \
            .annotate(latest_post=Max('post')) \
            .order_by('-latest_post')
        return queryset


class TopicDetail(RetrieveAPIView):
    serializer_class = TopicSerializer
    lookup_url_kwarg = 'topic_id'

    def get_queryset(self):
        return Topic.objects.all()
