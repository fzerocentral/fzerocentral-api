from django.db import models


class User(models.Model):
    username = models.CharField(max_length=30)
    post_count = models.IntegerField(default=0)

    class Levels(models.IntegerChoices):
        REGULAR = 0, "Regular"
        ADMIN = 1, "Admin"
        MOD = 2, "Mod"
    level = models.IntegerField(
        choices=Levels.choices, default=Levels.REGULAR)

    class JSONAPIMeta:
        resource_name = 'old_forum_users'
