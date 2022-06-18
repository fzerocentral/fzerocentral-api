from django.db import models


class Category(models.Model):
    title = models.CharField(max_length=200)
    order = models.IntegerField()

    class JSONAPIMeta:
        resource_name = 'old_forum_categories'
