from collections import defaultdict
from decimal import Decimal
from operator import itemgetter

from rest_framework.generics import (
    ListCreateAPIView, RetrieveUpdateDestroyAPIView)
from rest_framework.response import Response
from rest_framework.views import APIView

from chart_groups.utils import get_charts_in_hierarchy
from chart_types.utils import apply_format_spec
from core.utils import (
    add_ranks,
    delete_ordered_obj_prep,
    insert_ordered_obj_prep,
    reorder_obj_prep)
from filters.utils import apply_filter_spec, FilterSpec
from players.models import Player
from records.models import Record
from records.utils import make_record_ranking, sort_records_by_value
from .models import Ladder, LadderChartTag
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


class LadderRanking(APIView):

    def get(self, request, ladder_id):
        ladder = Ladder.objects.get(id=ladder_id)
        charts = get_charts_in_hierarchy(ladder.chart_group)
        chart_types = set([chart.chart_type for chart in charts])
        ladder_chart_tags = list(LadderChartTag.objects.filter(ladder=ladder))
        filter_spec = FilterSpec(ladder.filter_spec)

        if filter_spec.is_empty():
            all_records = Record.objects.filter(chart__in=charts)
        else:
            all_records = Record.objects.none()

            # Apply the filter spec to the records. Also ensure we only apply
            # the filters that each chart type recognizes.
            for chart_type in chart_types:
                ct_records = Record.objects.filter(
                    chart__in=charts, chart__chart_type=chart_type)
                ct_records = apply_filter_spec(ct_records, filter_spec)
                all_records |= ct_records

        # All the players in the ladder

        player_ids = all_records.values_list('player_id', flat=True).distinct()

        # Add more player info

        players = Player.objects.filter(id__in=player_ids).values(
            'id', 'username')
        players_data = {p['id']: dict(username=p['username']) for p in players}

        for r in all_records.order_by('player_id', '-date_achieved') \
                .distinct('player_id') \
                .values('player_id', 'date_achieved'):
            players_data[r['player_id']]['last_active'] = r['date_achieved']

        def chart_count_list():
            return [None] * len(charts)
        charts_data = []
        players_record_data: dict[list[dict | None]] = \
            defaultdict(chart_count_list)

        for chart_index, chart in enumerate(charts):

            records = Record.objects.filter(chart=chart)
            chart_tags = list(chart.chart_tags.all())

            # Tags applying to this chart for this ladder.
            applicable_tag_ids = (
                set([tag.id for tag in chart_tags])
                & set([lc_tag.chart_tag_id for lc_tag in ladder_chart_tags])
            )

            if not ladder_chart_tags:
                # No ladder formula; all charts are weighted 1.
                chart_weight = 1
            elif not applicable_tag_ids:
                # Chart is not counted in the ladder formula.
                chart_weight = 0
            else:
                # Chart is counted in the ladder formula. Check all the
                # applicable chart tags; lowest weight wins.
                chart_weight = min([
                    lc_tag.weight for lc_tag in ladder_chart_tags
                    if lc_tag.chart_tag_id in applicable_tag_ids])

            if not filter_spec.is_empty():
                records = apply_filter_spec(records, filter_spec)

            # Sort records best-first.
            records = sort_records_by_value(records, chart.id)

            records = records.values(
                'id', 'value', 'date_achieved', 'player_id')

            records = make_record_ranking(records)
            record_count = len(records)
            sr_value = records[0]['value']

            charts_data.append(dict(
                tag_ids=applicable_tag_ids,
                weight=chart_weight,
                record_count=record_count,
                sr_value=sr_value,
                order_ascending=chart.chart_type.order_ascending,
            ))

            for r in records:
                players_record_data[r['player_id']][chart_index] = dict(
                    rank=r['rank'],
                    value=r['value'],
                )

        chart_weight_total = sum([cd['weight'] for cd in charts_data])

        chart_tags_lookup = dict()
        for lc_tag in ladder_chart_tags:
            tag_id = lc_tag.chart_tag_id
            tag = lc_tag.chart_tag
            chart_tags_lookup[tag_id] = tag

        entries = []

        for player_id in player_ids:

            charts_record_data = players_record_data[player_id]

            # AF

            weighted_ranks = []
            for ci in range(len(charts)):
                if charts_record_data[ci] is None:
                    # No record for this chart: Use last rank + 1
                    rank = charts_data[ci]['record_count'] + 1
                else:
                    rank = charts_record_data[ci]['rank']
                weighted_ranks.append(charts_data[ci]['weight'] * rank)

            # To 3 decimal places, like 4.560
            af = sum(weighted_ranks) / chart_weight_total
            af_display = format(af, '.3f')

            # SRPR

            weighted_srprs = []
            for ci in range(len(charts)):
                if charts_record_data[ci] is None:
                    # No record for this chart: Use 0
                    chart_srpr = 0
                else:
                    sr_value = charts_data[ci]['sr_value']
                    if charts_data[ci]['order_ascending']:
                        chart_srpr = (
                            Decimal(sr_value)
                            / Decimal(charts_record_data[ci]['value']))
                    else:
                        chart_srpr = (
                            Decimal(charts_record_data[ci]['value'])
                            / Decimal(sr_value))
                weighted_srprs.append(charts_data[ci]['weight'] * chart_srpr)

            # Multiplying by 100 makes it a percentage:
            # 0.934497 -> 93.4497%
            srpr = (
                Decimal(100)
                * sum(weighted_srprs)
                / Decimal(chart_weight_total)
            )
            # To 3 decimal places, like 93.450%
            srpr_display = f"{srpr:.3f}%"

            last_active = players_data[player_id]['last_active']
            last_active_display = last_active.date().isoformat()

            entry = dict(
                player_id=player_id,
                player_username=players_data[player_id]['username'],
                af=af,
                af_display=af_display,
                srpr=srpr,
                srpr_display=srpr_display,
                last_active=last_active,
                last_active_display=last_active_display,
                totals=[],
            )

            # Totals

            record_values_by_tag = defaultdict(list)
            order_ascending_by_tag = dict()
            for ci in range(len(charts)):
                for tag_id in charts_data[ci]['tag_ids']:
                    if charts_record_data[ci] is None:
                        value = None
                    else:
                        value = charts_record_data[ci]['value']
                    record_values_by_tag[tag_id].append(value)
                    order_ascending_by_tag[tag_id] = \
                        charts_data[ci]['order_ascending']

            for tag_id, record_values in record_values_by_tag.items():

                if None in record_values:
                    if order_ascending_by_tag[tag_id]:
                        # Blank record invalidates the total.
                        total = None
                    else:
                        # Filter out the blank records and sum up the rest.
                        def not_none(r):
                            return r is not None
                        total = sum(filter(not_none, record_values))
                else:
                    # Sum up.
                    total = sum(record_values)

                # Format the total.
                tag = chart_tags_lookup[tag_id]
                format_spec = tag.primary_chart_type.format_spec
                if total is None:
                    total_value = None
                else:
                    total_value = apply_format_spec(format_spec, total)
                total_name = tag.total_name

                entry['totals'].append(dict(
                    name=total_name, value=total_value))

            entries.append(entry)

        entries.sort(key=itemgetter('af'))
        add_ranks(entries, 'af')

        return Response(entries)
