from charts.models import Chart
from .models import ChartGroup


def get_charts_in_hierarchy(chart_group: ChartGroup) -> list[Chart]:
    charts = []
    for child_group in chart_group.child_groups.order_by('order_in_parent'):
        charts.extend(get_charts_in_hierarchy(child_group))
    for chart in chart_group.charts.order_by('order_in_group'):
        charts.append(chart)
    return charts
