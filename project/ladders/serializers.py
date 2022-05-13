from rest_framework_json_api import serializers

from chart_groups.serializers_nested import ChartGroupIncludeSerializer
from chart_tags.serializers import ChartTagSerializer
from games.serializers import GameSerializer
from .models import Ladder, LadderChartTag


class LadderChartTagSerializer(serializers.ModelSerializer):
    # These related resources are available for inclusion with the
    # `include` query parameter.
    included_serializers = {
        'chart_tag': ChartTagSerializer,
    }

    class Meta:
        model = LadderChartTag
        fields = '__all__'


class LadderSerializer(serializers.ModelSerializer):
    included_serializers = {
        'chart_group': ChartGroupIncludeSerializer,
        'game': GameSerializer,
        'ladder_chart_tags': LadderChartTagSerializer,
    }

    class Meta:
        model = Ladder
        fields = [
            'name', 'filter_spec', 'kind', 'game', 'chart_group',
            'order_in_game_and_kind', 'ladder_chart_tags',
        ]
