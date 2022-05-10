from rest_framework.generics import (
    ListCreateAPIView, RetrieveUpdateDestroyAPIView)

from core.utils import filter_queryset_by_param
from .models import ChartType
from .serializers import ChartTypeSerializer


class ChartTypeIndex(ListCreateAPIView):
    serializer_class = ChartTypeSerializer

    def get_queryset(self):
        queryset = ChartType.objects.all().order_by('name')

        queryset = filter_queryset_by_param(
            self.request, 'game_id', queryset, 'game')
        queryset = filter_queryset_by_param(
            self.request, 'game_code', queryset, 'game__short_code')

        queryset = filter_queryset_by_param(
            self.request, 'filter_group_id', queryset, 'filter_groups')

        return queryset


class ChartTypeDetail(RetrieveUpdateDestroyAPIView):
    serializer_class = ChartTypeSerializer
    lookup_url_kwarg = 'chart_type_id'

    def get_queryset(self):
        return ChartType.objects.all()
