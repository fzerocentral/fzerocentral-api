from rest_framework_json_api import serializers

from .models import ChartType


class ChartTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChartType
        # Specify the fields explicitly to include m2m (filter_groups).
        fields = [
            'id', 'name', 'format_spec', 'order_ascending',
            'game', 'filter_groups']

    # Serialize format spec as a JSON encoded string, rather than a primitive
    # data structure.
    format_spec = serializers.JSONField(binary=True)
