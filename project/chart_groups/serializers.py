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


class ChartGroupHierarchySerializer(serializers.ModelSerializer):
    """
    Serializer for listing a hierarchy of groups and charts. Child elements are
    listed instead of parent elements, and certain fields can be omitted.
    """
    included_serializers = {
        'charts': ChartSerializer,
        'child_groups': 'chart_groups.serializers.ChartGroupHierarchySerializer',
    }

    class Meta:
        model = ChartGroup
        fields = ['id', 'name', 'order_in_parent', 'charts', 'child_groups']

    class JSONAPIMeta:
        # Here we hard-code the included_resources strings... if we need more
        # nesting depth than this, we should instead write a function that
        # generates this list of strings for any nesting depth N.
        included_resources = [
            'charts',
            'child_groups',
            'child_groups.charts',
            'child_groups.child_groups',
            'child_groups.child_groups.charts',
            'child_groups.child_groups.child_groups',
            'child_groups.child_groups.child_groups.charts',
        ]
