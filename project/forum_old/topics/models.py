from django.db import models

from ..forums.models import Forum


class Topic(models.Model):
    title = models.CharField(max_length=500)

    forum = models.ForeignKey(Forum, on_delete=models.RESTRICT)

    class JSONAPIMeta:
        resource_name = 'old_forum_topics'
