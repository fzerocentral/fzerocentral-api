from rest_framework.generics import ListAPIView, RetrieveAPIView

from .models import Chart
from .serializers import ChartSerializer


class ChartIndex(ListAPIView):
    serializer_class = ChartSerializer

    def get_queryset(self):
        queryset = Chart.objects.all()

        chart_group_id = self.request.query_params.get('chart_group_id')
        if chart_group_id is not None:
            queryset = queryset.filter(
                chart_group=chart_group_id).order_by('order_in_group')

        return queryset


class ChartDetail(RetrieveAPIView):
    serializer_class = ChartSerializer
    lookup_url_kwarg = 'chart_id'

    def get_queryset(self):
        return Chart.objects.all()
