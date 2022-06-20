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

        # Hide moved topics by default, because:
        # - They're only useful to list when they're recent, since whoever's
        # looking for the topic may not know that it moved.
        # But this is an old archive, with no recent posts.
        # - It requires extra logic to sort moved topics properly
        # with other topics.
        include_moved = self.request.query_params.get('include_moved', 'no')
        if include_moved != 'yes':
            queryset = queryset.exclude(status=Topic.Statuses.MOVED)

        # Order criteria:
        # 1. announcements first, then sticky, then others
        # 2. latest post ID
        queryset = queryset \
            .annotate(latest_post=Max('post')) \
            .order_by('-importance', '-latest_post')
        return queryset


class TopicDetail(RetrieveAPIView):
    serializer_class = TopicSerializer
    lookup_url_kwarg = 'topic_id'

    def get_queryset(self):
        return Topic.objects.all()
