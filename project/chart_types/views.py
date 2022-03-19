from rest_framework.generics import (
    ListCreateAPIView, RetrieveUpdateDestroyAPIView)

from .models import ChartType
from .serializers import ChartTypeSerializer


class ChartTypeIndex(ListCreateAPIView):
    serializer_class = ChartTypeSerializer

    def get_queryset(self):
        queryset = ChartType.objects.all().order_by('name')

        game_id = self.request.query_params.get('game_id')
        if game_id is not None:
            queryset = queryset.filter(game=game_id)

        filter_group_id = self.request.query_params.get('filter_group_id')
        if filter_group_id is not None:
            queryset = queryset.filter(filter_groups=filter_group_id)

        return queryset


class ChartTypeDetail(RetrieveUpdateDestroyAPIView):
    serializer_class = ChartTypeSerializer
    lookup_url_kwarg = 'chart_type_id'

    def get_queryset(self):
        return ChartType.objects.all()
