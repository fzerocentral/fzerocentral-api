from rest_framework.generics import ListAPIView, RetrieveAPIView

from .models import Game
from .serializers import GameSerializer


class GameIndex(ListAPIView):

    def get_queryset(self):
        return Game.objects.all().order_by('name')
    serializer_class = GameSerializer


class GameDetail(RetrieveAPIView):

    def get_queryset(self):
        return Game.objects.all()
    serializer_class = GameSerializer
    lookup_url_kwarg = 'game_id'
