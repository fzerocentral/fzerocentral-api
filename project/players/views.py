from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework_json_api.pagination import JsonApiPageNumberPagination

from .models import Player
from .serializers import PlayerSerializer


class PlayerPagination(JsonApiPageNumberPagination):
    max_page_size = 1000


class PlayerIndex(ListAPIView):
    serializer_class = PlayerSerializer

    # TODO: Instead of increasing the max page size, we probably want the
    # default max of 100 + the ability to search players by username.
    pagination_class = PlayerPagination

    def get_queryset(self):
        return Player.objects.all().order_by('username')


class PlayerDetail(RetrieveAPIView):
    serializer_class = PlayerSerializer
    lookup_url_kwarg = 'player_id'

    def get_queryset(self):
        return Player.objects.all()
