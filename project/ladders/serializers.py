from rest_framework_json_api import serializers

from .models import Ladder


class LadderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ladder
        exclude = ['date_created', 'date_modified']
