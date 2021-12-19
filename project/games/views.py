from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Game
from .serializers import GameSerializer


class GameIndex(APIView):

    def get(self, request):
        games = Game.objects.all()
        serializer = GameSerializer(games, many=True)
        return Response(dict(data=serializer.data), status=status.HTTP_200_OK)


class GameDetail(APIView):

    def get(self, request, game_pk):
        try:
            game = Game.objects.get(pk=game_pk)
        except Game.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = GameSerializer(game)
        return Response(dict(data=serializer.data), status=status.HTTP_200_OK)
