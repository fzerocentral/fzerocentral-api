# https://www.django-rest-framework.org/api-guide/serializers/
# https://django-rest-framework-json-api.readthedocs.io/en/stable/usage.html#serializers
from rest_framework_json_api import serializers

from .models import Game


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        exclude = ['date_created', 'date_modified']
