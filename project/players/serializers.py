from rest_framework_json_api import serializers

from .models import Player


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        exclude = ['date_created', 'date_modified']
