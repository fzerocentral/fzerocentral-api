from rest_framework.generics import ListAPIView, RetrieveAPIView

from core.utils import filter_queryset_by_param
from .models import Game
from .serializers import GameSerializer


class GameIndex(ListAPIView):
    serializer_class = GameSerializer

    def get_queryset(self):
        queryset = Game.objects.all().order_by('name')

        queryset = filter_queryset_by_param(
            self.request, 'name', queryset, 'name')
        queryset = filter_queryset_by_param(
            self.request, 'short_code', queryset, 'short_code')

        return queryset


class GameDetail(RetrieveAPIView):

    def get_queryset(self):
        return Game.objects.all()
    serializer_class = GameSerializer
    lookup_url_kwarg = 'game_id'
