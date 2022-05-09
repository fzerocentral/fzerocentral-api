from django.db import models


class Player(models.Model):
    username = models.CharField(max_length=25)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
