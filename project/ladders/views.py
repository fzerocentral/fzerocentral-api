from rest_framework.generics import (
    ListCreateAPIView, RetrieveUpdateDestroyAPIView)

from core.utils import (
    delete_ordered_obj_prep, insert_ordered_obj_prep, reorder_obj_prep)
from .models import Ladder
from .serializers import LadderSerializer


class LadderIndex(ListCreateAPIView):
    serializer_class = LadderSerializer

    def get_queryset(self):
        queryset = Ladder.objects.all()

        game_id = self.request.query_params.get('game_id')
        if game_id is not None:
            queryset = queryset.filter(
                game=game_id).order_by('order_in_game_and_kind')

        kind = self.request.query_params.get('kind')
        if kind is not None:
            queryset = queryset.filter(kind=kind)

        return queryset

    def create(self, request, *args, **kwargs):
        existing_ladders = Ladder.objects.filter(
            game=request.data['game']['id'],
            kind=request.data['kind'])
        # Prep before insertion.
        request = insert_ordered_obj_prep(
            request, 'order_in_game_and_kind', existing_ladders)
        # Insert the new ladder.
        return super().create(request, *args, **kwargs)


class LadderDetail(RetrieveUpdateDestroyAPIView):
    serializer_class = LadderSerializer
    lookup_url_kwarg = 'ladder_id'

    def get_queryset(self):
        return Ladder.objects.all()

    def patch(self, request, *args, **kwargs):
        ladder = self.get_object()
        gk_ladders = Ladder.objects.filter(game=ladder.game, kind=ladder.kind)
        # Prep before reorder (if any).
        request = reorder_obj_prep(
            request, 'order_in_game_and_kind', ladder, gk_ladders)
        # Edit ladder.
        return super().patch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        ladder = self.get_object()
        gk_ladders = Ladder.objects.filter(game=ladder.game, kind=ladder.kind)
        # Prep before delete.
        delete_ordered_obj_prep('order_in_game_and_kind', ladder, gk_ladders)
        # Delete ladder.
        return super().delete(request, *args, **kwargs)
