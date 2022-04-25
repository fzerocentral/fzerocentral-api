from django.db.models import F
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from charts.models import Chart
from filters.models import Filter
from filters.utils import apply_filter_spec, FilterSpec
from records.models import Record
from records.utils import (
    add_record_displays, make_record_ranking, sort_records_by_value)
from .models import ChartGroup
from .serializers import ChartGroupSerializer


class ChartGroupIndex(ListAPIView):
    serializer_class = ChartGroupSerializer

    def get_queryset(self):
        queryset = ChartGroup.objects.all().order_by('id')

        game_id = self.request.query_params.get('game_id')
        if game_id is not None:
            queryset = queryset.filter(game=game_id)

        parent_group_id = self.request.query_params.get('parent_group_id')
        if parent_group_id is not None:
            if parent_group_id == '':
                queryset = queryset.filter(parent_group__isnull=True)
            else:
                queryset = queryset.filter(parent_group=parent_group_id)
            queryset = queryset.order_by('order_in_parent')

        return queryset


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


class ChartGroupRanking(APIView):

    def get(self, request, group_id):
        chart_group = ChartGroup.objects.get(id=group_id)

        main_chart_id = self.request.query_params.get('main_chart_id')
        if main_chart_id:
            main_chart = Chart.objects.get(id=main_chart_id)
        else:
            main_chart = chart_group.charts.order_by('order_in_group').first()

        main_chart_records = None
        other_charts_records = []

        for chart in chart_group.charts.order_by('order_in_group'):
            queryset = Record.objects.filter(chart=chart)

            filter_spec_str = self.request.query_params.get('filters')
            if filter_spec_str is not None and filter_spec_str != '':
                queryset = apply_filter_spec(
                    queryset, FilterSpec(filter_spec_str), chart.chart_type)

            # Fetch more fields.
            queryset = queryset.annotate(
                player_username=F('player__username'))

            # Sort records best-first.
            queryset = sort_records_by_value(queryset, chart.id)

            records = queryset.values(
                'id', 'value', 'date_achieved',
                'player_id', 'player_username')

            records = make_record_ranking(records)

            # Add the filters of each record.
            # These do have to be fetched separately, since values()
            # doesn't work well with multivalued relations.
            # https://docs.djangoproject.com/en/dev/ref/models/querysets/#values-list
            for record in records:
                record['filters'] = Filter.objects.filter(record=record['id']) \
                    .values('id', 'name', 'filter_group_id')

            add_record_displays(records, chart.chart_type.format_spec)

            if chart.id == main_chart.id:
                main_chart_records = records
            else:
                other_charts_records.append(
                    {r['player_id']: r for r in records})

        record_rows = []

        # Each row gets:
        # - Main chart record (main chart records are in ranked order)
        # - Same player's record in other chart 1, other chart 2, etc. (other
        #   charts are in chart group order)
        for main_record in main_chart_records:
            player_id = main_record['player_id']
            record_rows.append(dict(
                main_record=main_record,
                other_records=[
                    chart_records.get(player_id)
                    for chart_records in other_charts_records]))

        return Response(record_rows)
