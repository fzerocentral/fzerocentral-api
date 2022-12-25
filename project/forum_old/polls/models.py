from django.db import models

from ..topics.models import Topic


class Poll(models.Model):
    title = models.CharField(max_length=500)

    topic = models.OneToOneField(Topic, on_delete=models.CASCADE)

    class JSONAPIMeta:
        resource_name = 'old_forum_polls'
