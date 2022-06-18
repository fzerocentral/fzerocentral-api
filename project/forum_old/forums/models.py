from django.db import models

from ..categories.models import Category


class Forum(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=2000)
    order = models.IntegerField()

    category = models.ForeignKey(
        Category, on_delete=models.RESTRICT, related_name='forums')

    class JSONAPIMeta:
        resource_name = 'old_forum_forums'
