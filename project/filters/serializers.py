from rest_framework_json_api import serializers

from .models import Filter


class FilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filter
        exclude = [
            'outgoing_filter_implications', 'date_created', 'date_modified']
