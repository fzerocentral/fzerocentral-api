from rest_framework_json_api import serializers

from .models import ChartType


class ChartTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChartType
        exclude = ['date_created', 'date_modified']
