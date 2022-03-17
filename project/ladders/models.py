from django.db import models

from chart_groups.models import ChartGroup
from games.models import Game


class Ladder(models.Model):
    name = models.CharField(max_length=100)
    filter_spec = models.CharField(max_length=200, blank=True)

    class Kinds(models.TextChoices):
        MAIN = 'main', "Main"
        SIDE = 'side', "Side"
    kind = models.CharField(
        max_length=10, choices=Kinds.choices, default=Kinds.SIDE)

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    chart_group = models.ForeignKey(ChartGroup, on_delete=models.CASCADE)
    # Positive integer specifying order of this ladder relative to
    # others with the same game and kind.
    order_in_game_and_kind = models.IntegerField()

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # There can't be two charts with the same game, kind, and
            # order-in-game-and-kind.
            models.UniqueConstraint(
                fields=['game', 'kind', 'order_in_game_and_kind'],
                name='unique_game_kind_order',
                # Don't enforce the constraint until the end of a transaction.
                # This makes it easier to rearrange the order of ladders.
                deferrable=models.Deferrable.DEFERRED)]
