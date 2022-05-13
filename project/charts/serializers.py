from rest_framework_json_api import serializers

from chart_groups.serializers_nested import ChartGroupIncludeSerializer
from .models import Chart


class ChartSerializer(serializers.ModelSerializer):
    # These related fields are available for inclusion with the `include`
    # query parameter.
    included_serializers = {
        'chart_group': ChartGroupIncludeSerializer,
    }

    class Meta:
        model = Chart
        fields = [
            'name', 'chart_group', 'order_in_group', 'chart_type',
            'chart_tags',
        ]
