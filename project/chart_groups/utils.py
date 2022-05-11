from collections import defaultdict
from operator import attrgetter

from django.db.models import Case, QuerySet, Value, When

from charts.models import Chart
from .models import ChartGroup


def get_charts_in_hierarchy(chart_group: ChartGroup) -> QuerySet:
    game = chart_group.game
    cg_lookup = defaultdict(list)
    for cg in game.chartgroup_set.all():
        cg_lookup[cg.parent_group_id].append(cg)
    for chart in Chart.objects.filter(chart_group__game=game):
        cg_lookup[chart.chart_group_id].append(chart)

    def visit_chart_group(current_cg):
        lookup_entry = cg_lookup[current_cg.id]
        if isinstance(lookup_entry[0], Chart):
            # Order charts and return them
            return sorted(lookup_entry, key=attrgetter('order_in_group'))
        else:
            # Order chart groups and return their combined visit results
            charts = []
            for child_group in sorted(
                    lookup_entry, key=attrgetter('order_in_parent')):
                charts.extend(visit_chart_group(child_group))
            return charts

    chart_list = visit_chart_group(chart_group)

    # The charts are in an order which aren't defined by a particular field.
    # We use Case-When to maintain this ordering in a QuerySet.
    # https://stackoverflow.com/a/69333396
    chart_ids = [c.id for c in chart_list]
    queryset = Chart.objects.filter(id__in=chart_ids)
    return queryset.order_by(
        'id',
        Case(
            *[When(id=chart_id, then=Value(i))
              for i, chart_id in enumerate(chart_ids)],
            default=None
        ).asc()
    )
