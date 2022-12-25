from django.db import models

from ..polls.models import Poll


class PollOption(models.Model):
    text = models.CharField(max_length=500)
    vote_count = models.IntegerField()

    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    option_number = models.PositiveIntegerField()

    class JSONAPIMeta:
        resource_name = 'old_forum_poll_options'

    class Meta:
        constraints = [
            # There can't be two options in the same poll with
            # the same option number.
            models.UniqueConstraint(
                'poll', 'option_number',
                name='unique_poll_option_number')]
