from rest_framework_json_api import serializers
from rest_framework_json_api.relations import ResourceRelatedField

from ..forums.serializers import ForumSerializer
from ..posts.models import Post
from ..posts.serializers import PostCompactSerializer
from .models import Topic


class TopicSerializer(serializers.ModelSerializer):
    # Model-class properties that should be serialized like foreign keys.
    first_post = ResourceRelatedField(queryset=Post.objects)
    last_post = ResourceRelatedField(queryset=Post.objects)

    # These related fields are available for inclusion with the `include`
    # query parameter.
    included_serializers = {
        'forum': ForumSerializer,
        'first_post': PostCompactSerializer,
        'last_post': PostCompactSerializer,
    }

    class Meta:
        model = Topic
        fields = [
            'title', 'has_poll', 'is_news', 'status', 'importance',
            'forum', 'first_post', 'last_post',
        ]
