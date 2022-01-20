from django.db import models

from filter_groups.models import FilterGroup
from games.models import Game


class ChartType(models.Model):
    name = models.CharField(max_length=200)
    format_spec = models.JSONField(verbose_name="Format specification")
    order_ascending = models.BooleanField()

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    filter_groups = models.ManyToManyField(FilterGroup, through='CTFG')

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)


class CTFG(models.Model):
    chart_type = models.ForeignKey(ChartType, on_delete=models.CASCADE)
    filter_group = models.ForeignKey(FilterGroup, on_delete=models.CASCADE)

    # Whether to show the filter group by default when filtering a chart of
    # this chart type.
    show_by_default = models.BooleanField(default=True)

    # Positive integer specifying order of this filter group relative to
    # others for this chart type.
    order_in_chart_type = models.IntegerField()

    class Meta:
        constraints = [
            # There can't be two filter groups with the same
            # order-in-chart-type for the same chart type.
            models.UniqueConstraint(
                fields=['chart_type', 'order_in_chart_type'],
                name='unique_ctfg_charttype_order',
                # Don't enforce the constraint until the end of a transaction.
                # This makes it easier to rearrange the order of FGs in a CT.
                deferrable=models.Deferrable.DEFERRED)]
