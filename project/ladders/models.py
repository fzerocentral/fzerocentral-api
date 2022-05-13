from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from chart_groups.models import ChartGroup
from chart_tags.models import ChartTag
from games.models import Game


class Ladder(models.Model):
    name = models.CharField(max_length=100)
    filter_spec = models.CharField(max_length=200, blank=True)

    class Kinds(models.TextChoices):
        MAIN = 'main', "Main"
        SIDE = 'side', "Side"
    kind = models.CharField(
        max_length=10, choices=Kinds.choices, default=Kinds.SIDE)

    # Each ladder belongs to a game for organization purposes.
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    # Charts that are available under this ladder.
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


class LadderChartTag(models.Model):
    ladder = models.ForeignKey(
        Ladder, on_delete=models.CASCADE, related_name='ladder_chart_tags')
    chart_tag = models.ForeignKey(
        ChartTag, on_delete=models.CASCADE, related_name='ladder_chart_tags')

    # Relative weights of different charts in ladder ranking calculations.
    weight = models.DecimalField(
        default=Decimal(1),
        max_digits=4,
        decimal_places=3,
        validators=[
            MaxValueValidator(Decimal(1)),
            MinValueValidator(Decimal(0)),
        ],
    )
