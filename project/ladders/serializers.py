from rest_framework_json_api import serializers

from games.serializers import GameSerializer
from .models import Ladder


class LadderSerializer(serializers.ModelSerializer):
    # These related fields are available for inclusion with the `include`
    # query parameter.
    included_serializers = {
        'game': GameSerializer,
    }

    class Meta:
        model = Ladder
        exclude = ['date_created', 'date_modified']
