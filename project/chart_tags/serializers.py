from rest_framework_json_api import serializers

from .models import ChartTag


class ChartTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChartTag
        exclude = ['charts']
