from rest_framework.generics import (
    ListAPIView, RetrieveAPIView)

from core.utils import filter_queryset_by_param
from .models import ChartTag
from .serializers import ChartTagSerializer


class ChartTagIndex(ListAPIView):
    serializer_class = ChartTagSerializer

    def get_queryset(self):
        queryset = ChartTag.objects.all().order_by('name')

        queryset = filter_queryset_by_param(
            self.request, 'ladder_id',
            queryset, 'laddercharttag__ladder')

        return queryset


class ChartTagDetail(RetrieveAPIView):
    serializer_class = ChartTagSerializer
    lookup_url_kwarg = 'chart_tag_id'

    def get_queryset(self):
        return ChartTag.objects.all()
