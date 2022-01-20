from django.db import models

from charts.models import Chart
from filters.models import Filter
from players.models import Player


class Record(models.Model):
    value = models.IntegerField()
    date_achieved = models.DateTimeField()

    chart = models.ForeignKey(Chart, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    filters = models.ManyToManyField(Filter)

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
