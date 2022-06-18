from django.db import models

from ..topics.models import Topic
from ..users.models import User


class Post(models.Model):
    subject = models.CharField(max_length=500)
    text = models.CharField(max_length=1000000)
    time = models.DateTimeField()
    # Optional username for guest posts
    username = models.CharField(max_length=30)

    topic = models.ForeignKey(Topic, on_delete=models.RESTRICT)
    # Guest posts have this set to null
    poster = models.ForeignKey(User, on_delete=models.RESTRICT, null=True)

    class JSONAPIMeta:
        resource_name = 'old_forum_posts'
