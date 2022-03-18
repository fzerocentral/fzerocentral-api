from rest_framework.generics import (
    ListAPIView, ListCreateAPIView,
    RetrieveAPIView, RetrieveUpdateDestroyAPIView)

from charts.models import Chart
from core.utils import (
    delete_ordered_obj_prep, insert_ordered_obj_prep, reorder_obj_prep)
from .models import ChartType, CTFG
from .serializers import ChartTypeSerializer, CTFGSerializer


class ChartTypeIndex(ListAPIView):
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


class ChartTypeDetail(RetrieveAPIView):
    serializer_class = ChartTypeSerializer
    lookup_url_kwarg = 'chart_type_id'

    def get_queryset(self):
        return ChartType.objects.all()


class CTFGIndex(ListCreateAPIView):
    serializer_class = CTFGSerializer

    def get_queryset(self):
        queryset = CTFG.objects.all().order_by('id')

        chart_type_id = self.request.query_params.get('chart_type_id')
        if chart_type_id is not None:
            queryset = queryset.filter(chart_type=chart_type_id).order_by(
                'order_in_chart_type')

        chart_id = self.request.query_params.get('chart_id')
        if chart_id is not None:
            chart = Chart.objects.get(id=chart_id)
            queryset = queryset.filter(chart_type=chart.chart_type).order_by(
                'order_in_chart_type')

        return queryset

    def create(self, request, *args, **kwargs):
        existing_ctfgs = CTFG.objects.filter(
            chart_type=request.data['chart_type']['id'])
        # Prep before insertion.
        request = insert_ordered_obj_prep(
            request, 'order_in_chart_type', existing_ctfgs)
        # Insert the new CTFG.
        return super().create(request, *args, **kwargs)


class CTFGDetail(RetrieveUpdateDestroyAPIView):
    serializer_class = CTFGSerializer
    lookup_url_kwarg = 'ctfg_id'

    def get_queryset(self):
        return CTFG.objects.all()

    def patch(self, request, *args, **kwargs):
        ctfg = self.get_object()
        ct_ctfgs = CTFG.objects.filter(chart_type=ctfg.chart_type)
        # Prep before reorder (if any).
        request = reorder_obj_prep(
            request, 'order_in_chart_type', ctfg, ct_ctfgs)
        # Edit CTFG.
        return super().patch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        ctfg = self.get_object()
        ct_ctfgs = CTFG.objects.filter(chart_type=ctfg.chart_type)
        # Prep before delete.
        delete_ordered_obj_prep('order_in_chart_type', ctfg, ct_ctfgs)
        # Delete CTFG.
        return super().delete(request, *args, **kwargs)
