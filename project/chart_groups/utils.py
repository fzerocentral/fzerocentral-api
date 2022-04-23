from charts.models import Chart
from .models import ChartGroup


def get_charts_in_hierarchy(chart_group: ChartGroup) -> list[Chart]:
    charts = []
    for child_group in chart_group.child_groups.all():
        charts.extend(get_charts_in_hierarchy(child_group))
    for chart in chart_group.charts.all():
        charts.append(chart)
    return charts
