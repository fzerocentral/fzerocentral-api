from django.db.models import F
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from chart_groups.utils import get_charts_in_hierarchy
from core.utils import require_one_of_params
from filters.models import Filter
from filters.utils import apply_filter_spec, FilterSpec
from ladders.models import Ladder
from records.models import Record
from records.utils import (
    add_record_displays, make_record_ranking, sort_records_by_value)
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

        # May or may not stay a queryset from here on out.
        charts = queryset

        ladder_id = self.request.query_params.get('ladder_id')
        if ladder_id is not None:
            ladder = Ladder.objects.get(id=ladder_id)
            charts = get_charts_in_hierarchy(ladder.chart_group)

        return charts


class ChartDetail(RetrieveAPIView):
    serializer_class = ChartSerializer
    lookup_url_kwarg = 'chart_id'

    def get_queryset(self):
        return Chart.objects.all()


class ChartRanking(APIView):

    def get(self, request, chart_id):
        chart = Chart.objects.get(id=chart_id)

        queryset = Record.objects.filter(chart=chart_id)

        filter_spec = FilterSpec.from_query_params(self.request.query_params)
        queryset = apply_filter_spec(
            queryset, filter_spec, chart.chart_type)

        # Sort records best-first.
        queryset = sort_records_by_value(queryset, chart_id)

        # Fetch more fields.
        queryset = queryset.annotate(
            player_username=F('player__username'))

        records = queryset.values(
            'id', 'value', 'date_achieved', 'player_id', 'player_username')

        records = make_record_ranking(records)

        # Add the filters of each record.
        # These do have to be fetched separately, since values()
        # doesn't work well with multivalued relations.
        # https://docs.djangoproject.com/en/dev/ref/models/querysets/#values-list
        for record in records:
            record['filters'] = Filter.objects.filter(record=record['id']) \
                .values('id', 'name', 'filter_group_id')

        add_record_displays(records, chart.chart_type.format_spec)

        return Response(records)


class ChartOtherRecords(APIView):
    """
    Given a chart and a list of players, get those players' records for the
    other charts in the same chart group.
    """
    def get(self, request, chart_id):
        chart = Chart.objects.get(id=chart_id)
        chart_group = chart.chart_group
        if not chart_group.show_charts_together:
            raise ValueError(
                "This endpoint only applies to chart groups where"
                " show_charts_together is true.")

        # Must specify the players we're getting records for. This is
        # generally the set of players who have records in the specified
        # chart.
        require_one_of_params(request, 'player_ids')

        # Comma separated IDs like 1,3,9,24
        player_ids_str = self.request.query_params.get('player_ids')
        player_ids = player_ids_str.split(',')

        # Charts in the group other than the specified chart
        other_charts = list(
            chart_group.charts.order_by('order_in_group')
                .exclude(id=chart.id))

        other_charts_records = dict()

        for chart in other_charts:
            queryset = Record.objects.filter(chart=chart)

            queryset = queryset.filter(player__in=player_ids)

            filter_spec = FilterSpec.from_query_params(
                self.request.query_params)
            queryset = apply_filter_spec(
                queryset, filter_spec, chart.chart_type)

            # Sort records best-first.
            queryset = sort_records_by_value(queryset, chart.id)

            records = queryset.values(
                'id', 'value', 'player_id')

            # Probably won't really need the ranks, but we do need to
            # limit to one record per player.
            records = make_record_ranking(records)

            add_record_displays(records, chart.chart_type.format_spec)

            other_charts_records[chart.id] = \
                {r['player_id']: r for r in records}

        return Response(other_charts_records)


class ChartRecordHistory(APIView):

    def get(self, request, chart_id):
        chart = Chart.objects.get(id=chart_id)

        # Latest date first. The secondary ordering by record ID makes the
        # result order repeatable.
        queryset = Record.objects.filter(chart=chart_id).order_by(
            '-date_achieved', '-id')

        player_id = self.request.query_params.get('player_id')
        if player_id is not None:
            queryset = queryset.filter(player=player_id)

        filter_spec = self.request.query_params.get('filters')
        if filter_spec is not None and filter_spec != '':
            queryset = apply_filter_spec(
                queryset, FilterSpec(filter_spec), chart.chart_type)

        # Fetch more fields.
        queryset = queryset.annotate(
            player_username=F('player__username'))

        records = queryset.values(
            'id', 'value', 'date_achieved', 'player_id', 'player_username')

        # What to do with improvements among the set of records over time:
        # flag which ones are improvements or not, or filter out the
        # non-improvements.
        improvements_option = self.request.query_params.get(
            'improvements', 'flag')
        if improvements_option == 'flag':
            # Flag each record as an improvement over previous records or not.
            self.flag_improvements(records, chart.chart_type)
        elif improvements_option == 'filter':
            # Filter out non-improvements. So, strictly a PB/WR history.
            records = self.filter_to_improvements_only(
                records, chart.chart_type)
        else:
            raise ValueError(
                f"Unrecognized improvements option: {improvements_option}")

        # Add the filters of each record.
        for record in records:
            record['filters'] = Filter.objects.filter(record=record['id']) \
                .values('id', 'name', 'filter_group_id')

        add_record_displays(records, chart.chart_type.format_spec)

        return Response(records)

    @classmethod
    def flag_improvements(cls, records, chart_type):
        """
        At this point we know the records are sorted from latest date first.
        Iterate in reverse, from earliest date first, and figure out which
        records are improvements over all previous records.
        Flag each record as an improvement or not.
        """
        best_so_far = None
        for record in reversed(records):
            if cls.record_is_improvement(
                    record['value'], best_so_far, chart_type):
                best_so_far = record['value']
                record['is_improvement'] = True
            else:
                record['is_improvement'] = False

    @classmethod
    def filter_to_improvements_only(cls, records, chart_type):
        improvements_only = []
        best_so_far = None
        # While looking for improvements, iterate from earliest date first.
        for record in reversed(records):
            if cls.record_is_improvement(
                    record['value'], best_so_far, chart_type):
                best_so_far = record['value']
                # Add to start of list, to construct a list which starts from
                # latest date first.
                improvements_only.insert(0, record)
        return improvements_only

    @staticmethod
    def record_is_improvement(value, best_so_far, chart_type):
        """
        If value is a better record than best_so_far, return true. If worse
        or tied, return false. "better"/"worse" is determined by the chart_type.
        """
        if best_so_far is None:
            return True
        elif chart_type.order_ascending:
            return value < best_so_far
        else:
            # Descending
            return value > best_so_far
