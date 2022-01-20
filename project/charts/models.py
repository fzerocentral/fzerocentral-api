from django.db import models

from chart_groups.models import ChartGroup
from chart_types.models import ChartType


class Chart(models.Model):
    name = models.CharField(max_length=200)

    chart_group = models.ForeignKey(
        ChartGroup, on_delete=models.CASCADE, related_name='charts')
    # Positive integer specifying order of this chart group relative to
    # others under the same parent.
    order_in_group = models.IntegerField()

    chart_type = models.ForeignKey(ChartType, on_delete=models.RESTRICT)

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # There can't be two charts with the same group and
            # order-in-group.
            models.UniqueConstraint(
                'chart_group', 'order_in_group',
                name='unique_chart_group_order')]
