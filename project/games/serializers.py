# https://www.django-rest-framework.org/api-guide/serializers/
from rest_framework import serializers

from .models import Game


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        exclude = ['date_created', 'date_modified']
