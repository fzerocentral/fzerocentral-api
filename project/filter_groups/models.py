from django.db import models

from games.models import Game


class FilterGroup(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=2000)

    class Kinds(models.TextChoices):
        SELECT = 'select', "Select"
        NUMERIC = 'numeric', "Numeric"
    kind = models.CharField(
        max_length=10, choices=Kinds.choices, default=Kinds.SELECT)

    # Whether to show the filter group by default when filtering a chart that
    # it's on.
    show_by_default = models.BooleanField(default=True)

    # Filter groups already are linked to chart types, which are linked to
    # a game. However, for organizational purposes, it makes sense to link
    # filter groups to a game.
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    # Positive integer specifying order of this filter group relative to
    # others for this game.
    order_in_game = models.IntegerField()

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}, for {self.game.name}"
