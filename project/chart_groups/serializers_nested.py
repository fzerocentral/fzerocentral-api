# This separate serializers module helps to avoid circular imports
# between different apps' serializer modules.

from rest_framework_json_api import serializers

from .models import ChartGroup


class ChartGroupIncludeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChartGroup
        fields = ['id', 'name', 'show_charts_together']
