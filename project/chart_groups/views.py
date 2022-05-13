from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from core.utils import filter_queryset_by_param
from .models import ChartGroup
from .serializers import ChartGroupSerializer


class ChartGroupIndex(ListAPIView):
    serializer_class = ChartGroupSerializer

    def get_queryset(self):
        queryset = ChartGroup.objects.all().order_by('id')

        queryset = filter_queryset_by_param(
            self.request, 'game_id', queryset, 'game')
        queryset = filter_queryset_by_param(
            self.request, 'game_code', queryset, 'game__short_code')

        parent_group_id = self.request.query_params.get('parent_group_id')
        if parent_group_id is not None:
            if parent_group_id == '':
                queryset = queryset.filter(parent_group__isnull=True)
            else:
                queryset = queryset.filter(parent_group=parent_group_id)
            queryset = queryset.order_by('order_in_parent')

        return queryset \
            .select_related('game', 'parent_group') \
            .prefetch_related('charts')


class ChartGroupDetail(RetrieveAPIView):

    def get_queryset(self):
        return ChartGroup.objects.all()
    serializer_class = ChartGroupSerializer
    lookup_url_kwarg = 'group_id'


class ChartGroupHierarchy(APIView):

    @classmethod
    def visit_child_group(cls, cg):
        hierarchy = []
        if cg.child_groups.exists():
            for child_group in cg.child_groups.order_by('order_in_parent'):
                hierarchy.append(dict(
                    name=child_group.name,
                    chart_group_id=child_group.id,
                    show_charts_together=child_group.show_charts_together,
                    items=cls.visit_child_group(child_group),
                ))
        else:
            for chart in cg.charts.order_by('order_in_group'):
                hierarchy.append(dict(
                    name=chart.name,
                    chart_id=chart.id,
                ))
        return hierarchy

    def get(self, request, group_id):
        chart_group = ChartGroup.objects.get(id=group_id)
        hierarchy = self.visit_child_group(chart_group)
        return Response(hierarchy)
