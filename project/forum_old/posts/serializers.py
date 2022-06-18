from rest_framework_json_api import serializers

from ..users.serializers import UserSerializer
from .models import Post


class PostSerializer(serializers.ModelSerializer):
    # These related fields are available for inclusion with the `include`
    # query parameter.
    included_serializers = {
        'poster': UserSerializer,
    }

    class Meta:
        model = Post
        fields = '__all__'
