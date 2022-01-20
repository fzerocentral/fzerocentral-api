from rest_framework_json_api import serializers

from .models import FilterGroup


class FilterGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilterGroup
        exclude = ['date_created', 'date_modified']
