from rest_framework_json_api import serializers

from ..forums.serializers import ForumSerializer
from .models import Topic


class TopicSerializer(serializers.ModelSerializer):
    # These related fields are available for inclusion with the `include`
    # query parameter.
    included_serializers = {
        'forum': ForumSerializer,
    }

    class Meta:
        model = Topic
        fields = [
            'title', 'has_poll', 'is_news', 'status', 'importance', 'forum']
