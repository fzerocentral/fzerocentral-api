from django.db import models

from filter_groups.models import FilterGroup
from games.models import Game


class ChartType(models.Model):
    name = models.CharField(max_length=200)
    format_spec = models.JSONField(verbose_name="Format specification")
    order_ascending = models.BooleanField()

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    filter_groups = models.ManyToManyField(
        FilterGroup, related_name='chart_types')

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
