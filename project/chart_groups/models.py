from django.db import models

from games.models import Game


class ChartGroup(models.Model):
    name = models.CharField(max_length=200)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)

    # A game has a hierarchy of chart groups.
    # The top-level chart group has no parent.
    parent_group = models.ForeignKey(
        'ChartGroup', on_delete=models.SET_NULL, null=True,
        related_name='child_groups')

    # Positive integer specifying order of this chart group relative to
    # others under the same parent.
    order_in_parent = models.IntegerField()

    # Whether it makes sense to show rankings of this chart group's charts
    # in a single table. For example, course time, lap time, and max speed
    # for a particular course in an F-Zero game.
    show_charts_together = models.BooleanField(default=False)

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # There can't be two chart groups with the same parent and
            # order-in-parent.
            # Also, there can't be two top-level chart groups (i.e. null
            # parent) with the same order-in-parent (this represents their
            # order at the game's top level).
            models.UniqueConstraint(
                'parent_group', 'order_in_parent',
                name='unique_chartgroup_parent_order')]

    # TODO: Enforce the rule that a chart group's children must be all chart
    # groups, or all charts, not a mix of both. Could potentially check this
    # in ChartGroup.save() and Chart.save().
