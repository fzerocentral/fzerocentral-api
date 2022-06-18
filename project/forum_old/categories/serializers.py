from rest_framework_json_api import serializers

from ..forums.serializers import ForumSerializer
from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    # These related fields are available for inclusion with the `include`
    # query parameter.
    included_serializers = {
        'forums': ForumSerializer,
    }

    class Meta:
        model = Category
        fields = [
            'id', 'title', 'order', 'forums']
