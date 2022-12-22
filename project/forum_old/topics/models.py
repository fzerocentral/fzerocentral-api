from django.db import models

from ..forums.models import Forum


class Topic(models.Model):
    title = models.CharField(max_length=500)
    has_poll = models.BooleanField(default=False)
    is_news = models.BooleanField(default=False)

    class Statuses(models.IntegerChoices):
        UNLOCKED = 0, "Unlocked"
        LOCKED = 1, "Locked"
        MOVED = 2, "Moved"
    status = models.IntegerField(
        choices=Statuses.choices, default=Statuses.UNLOCKED)

    class ImportanceLevels(models.IntegerChoices):
        NORMAL = 0, "Normal"
        STICKY = 1, "Sticky"
        ANNOUNCEMENT = 2, "Announcement"
    importance = models.IntegerField(
        choices=ImportanceLevels.choices, default=ImportanceLevels.NORMAL)

    forum = models.ForeignKey(Forum, on_delete=models.RESTRICT)

    class JSONAPIMeta:
        resource_name = 'old_forum_topics'

    @property
    def first_post(self):
        return self.post_set.order_by('time').first()

    @property
    def last_post(self):
        return self.post_set.order_by('time').last()

    @property
    def post_count(self):
        return self.post_set.count()
