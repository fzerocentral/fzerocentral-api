from django.db import models

from chart_types.models import ChartType
from charts.models import Chart
from games.models import Game


class ChartTag(models.Model):
    name = models.CharField(max_length=50)
    # Name for this tag's total time/score, like "Lap total".
    total_name = models.CharField(max_length=50)

    # Belongs to a game.
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    # Chart type which determines the format spec and order direction
    # for this tag's total.
    primary_chart_type = models.ForeignKey(
        ChartType, on_delete=models.RESTRICT)
    # Each chart can have one or more chart tags. This allows defining
    # arbitrary groupings of charts, for the purpose of defining total
    # times/scores, defining weighted ranking formulas for ladders, etc.
    charts = models.ManyToManyField(Chart, related_name='chart_tags')

    def save(self, *args, **kwargs):
        if not self.total_name:
            self.total_name = f"{self.name} total"
        super().save(*args, **kwargs)
