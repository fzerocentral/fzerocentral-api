from rest_framework_json_api import serializers

from games.serializers import GameSerializer
from .models import FilterGroup


class FilterGroupSerializer(serializers.ModelSerializer):
    # These related resources are available for inclusion with the
    # `include` query parameter.
    included_serializers = {
        'game': GameSerializer,
    }

    class Meta:
        model = FilterGroup
        exclude = ['date_created', 'date_modified']
