from rest_framework.generics import (
    ListCreateAPIView, RetrieveUpdateDestroyAPIView)

from charts.models import Chart
from core.utils import (
    delete_ordered_obj_prep, insert_ordered_obj_prep, reorder_obj_prep)
from .models import FilterGroup
from .serializers import FilterGroupSerializer


class FilterGroupIndex(ListCreateAPIView):
    serializer_class = FilterGroupSerializer

    def get_queryset(self):
        # It should be most common to get FGs within a particular game, so by
        # default, we order in a way that makes sense there.
        queryset = FilterGroup.objects.all().order_by('order_in_game')

        game_id = self.request.query_params.get('game_id')
        if game_id is not None:
            queryset = queryset.filter(game=game_id)

        chart_type_id = self.request.query_params.get('chart_type_id')
        if chart_type_id is not None:
            queryset = queryset.filter(chart_types=chart_type_id)

        chart_id = self.request.query_params.get('chart_id')
        if chart_id is not None:
            chart = Chart.objects.get(id=chart_id)
            queryset = queryset.filter(chart_types=chart.chart_type_id)

        return queryset

    def create(self, request, *args, **kwargs):
        existing_fgs = FilterGroup.objects.filter(
            game=request.data['game']['id'])
        # Prep before insertion.
        request = insert_ordered_obj_prep(
            request, 'order_in_game', existing_fgs)
        # Insert the new FG.
        return super().create(request, *args, **kwargs)


class FilterGroupDetail(RetrieveUpdateDestroyAPIView):
    serializer_class = FilterGroupSerializer
    lookup_url_kwarg = 'group_id'

    def get_queryset(self):
        return FilterGroup.objects.all()

    def patch(self, request, *args, **kwargs):
        fg = self.get_object()
        game_fgs = FilterGroup.objects.filter(game=fg.game)
        # Prep before reorder (if any).
        request = reorder_obj_prep(
            request, 'order_in_game', fg, game_fgs)
        # Edit FG.
        return super().patch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        fg = self.get_object()
        game_fgs = FilterGroup.objects.filter(game=fg.game)
        # Prep before delete.
        delete_ordered_obj_prep('order_in_game', fg, game_fgs)
        # Delete FG.
        return super().delete(request, *args, **kwargs)
