from django.db import models


class Game(models.Model):
    name = models.CharField(max_length=200, unique=True)
    short_code = models.CharField(max_length=20, unique=True)

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
