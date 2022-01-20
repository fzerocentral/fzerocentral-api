from rest_framework_json_api import serializers

from filters.serializers import FilterSerializer
from .models import Record


class RecordIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = Record
        exclude = ['date_created', 'date_modified']


class RecordSerializer(RecordIndexSerializer):
    # Available included resources (e.g. ?include=filters)
    included_serializers = {
        'filters': FilterSerializer,
    }
