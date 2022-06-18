from django.db import models


class User(models.Model):
    username = models.CharField(max_length=30)

    class JSONAPIMeta:
        resource_name = 'old_forum_users'
