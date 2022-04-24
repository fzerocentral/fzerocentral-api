from rest_framework_json_api import serializers

from charts.serializers import ChartSerializer
from .models import ChartGroup


class ChartGroupSerializer(serializers.ModelSerializer):
    # These related fields are available for inclusion with the `include`
    # query parameter.
    included_serializers = {
        'charts': ChartSerializer,
    }

    class Meta:
        model = ChartGroup
        fields = [
            'id', 'name', 'game', 'parent_group', 'order_in_parent',
            'show_charts_together', 'charts']
