from rest_framework_json_api import serializers

from .models import PollOption


class PollOptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = PollOption
        fields = [
            'text', 'vote_count', 'poll',
        ]
