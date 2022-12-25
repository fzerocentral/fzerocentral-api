import re

from django.db import models

from ..topics.models import Topic
from ..users.models import User


class Post(models.Model):
    subject = models.CharField(max_length=500)
    raw_text = models.CharField(max_length=1000000)
    time = models.DateTimeField()
    edit_time = models.DateTimeField(null=True)
    # Optional username for guest posts
    username = models.CharField(max_length=30)

    topic = models.ForeignKey(Topic, on_delete=models.RESTRICT)
    # Guest posts have this set to null
    poster = models.ForeignKey(User, on_delete=models.RESTRICT, null=True)

    class JSONAPIMeta:
        resource_name = 'old_forum_posts'

    # Post text may have codes like {pi=1234}, which indicates that the
    # text contents of post 1234 should be substituted in place of the
    # code. Basically a way of including a post within another post.
    post_include_regex = re.compile(r'{pi=(\d+)}')

    @property
    def text(self):
        """
        Pre-process raw_text from the database, and output text for the API.
        """
        text = self.raw_text

        for match in self.post_include_regex.finditer(text):
            post_id = match.groups()[0]
            pi_text = match.string[match.start():match.end()]
            included_post_text = Post.objects.get(id=post_id).text
            text = text.replace(pi_text, included_post_text)

        return text
