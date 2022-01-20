from rest_framework_json_api import serializers

from .models import ChartType, CTFG


class ChartTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChartType
        exclude = ['date_created', 'date_modified']


class CTFGSerializer(serializers.ModelSerializer):
    class Meta:
        model = CTFG
        fields = '__all__'
        resource_name = 'chart-type-filter-groups'
