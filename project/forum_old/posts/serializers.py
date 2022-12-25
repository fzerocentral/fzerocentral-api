from rest_framework_json_api import serializers

from ..users.serializers import UserSerializer
from .models import Post


class PostSerializer(serializers.ModelSerializer):
    # These related fields are available for inclusion with the `include`
    # query parameter.
    included_serializers = {
        'poster': UserSerializer,
    }

    class Meta:
        model = Post
        fields = [
            'subject', 'time', 'edit_time', 'username', 'topic', 'poster',
            # text instead of raw_text
            'text',
        ]


class PostCompactSerializer(serializers.ModelSerializer):
    """
    More compact response, most notably omitting post text.
    """

    # These related fields are available for inclusion with the `include`
    # query parameter.
    included_serializers = {
        'poster': UserSerializer,
    }

    class Meta:
        model = Post
        fields = [
            'subject', 'time', 'username', 'topic', 'poster',
        ]
