from django.db import models

from charts.models import Chart
from games.models import Game


class ChartTag(models.Model):
    name = models.CharField(max_length=50)
    # Short name should generally be for naming the total time/score. For
    # example, short name of "Lap" gets a total of "Lap total", which is
    # more brief than, say, "Best lap total".
    short_name = models.CharField(max_length=200)

    # Belongs to a game.
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    # Each chart can have one or more chart tags. This allows defining
    # arbitrary groupings of charts, for the purpose of defining total
    # times/scores, defining weighted ranking formulas for ladders, etc.
    charts = models.ManyToManyField(Chart, related_name='chart_tags')

    def save(self, *args, **kwargs):
        if not self.short_name:
            self.short_name = self.name
        super().save(*args, **kwargs)
