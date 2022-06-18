from rest_framework_json_api import serializers

from .models import Forum


class ForumSerializer(serializers.ModelSerializer):

    class Meta:
        model = Forum
        fields = '__all__'
