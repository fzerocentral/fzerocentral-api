from rest_framework_json_api import serializers

from .models import Chart


class ChartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chart
        exclude = ['date_created', 'date_modified']
