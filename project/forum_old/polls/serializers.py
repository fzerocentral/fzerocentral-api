from rest_framework_json_api import serializers

from .models import Poll


class PollSerializer(serializers.ModelSerializer):

    class Meta:
        model = Poll
        fields = [
            'title', 'topic',
        ]
