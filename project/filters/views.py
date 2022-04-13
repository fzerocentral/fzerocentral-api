from rest_framework.generics import (
    ListCreateAPIView, RetrieveUpdateDestroyAPIView)
from rest_framework_json_api.views import RelationshipView

from .models import Filter
from .serializers import FilterSerializer
from .utils import apply_name_search


class FilterIndex(ListCreateAPIView):
    serializer_class = FilterSerializer

    def get_queryset(self):
        queryset = Filter.objects.all().order_by('name')

        # Comma separated IDs like 1,3,9,24
        filter_ids = self.request.query_params.get('filter_ids')
        if filter_ids is not None and filter_ids != '':
            queryset = queryset.filter(id__in=filter_ids.split(','))

        filter_group_id = self.request.query_params.get('filter_group_id')
        if filter_group_id is not None:
            queryset = queryset.filter(filter_group=filter_group_id)

        usage_type = self.request.query_params.get('usage_type')
        if usage_type is not None:
            queryset = queryset.filter(usage_type=usage_type)

        implies_filter_id = self.request.query_params.get('implies_filter_id')
        if implies_filter_id is not None:
            queryset = queryset.filter(
                outgoing_filter_implications=implies_filter_id)

        implied_by_filter_id = self.request.query_params.get(
            'implied_by_filter_id')
        if implied_by_filter_id is not None:
            queryset = queryset.filter(
                incoming_filter_implications=implied_by_filter_id)

        # From here on, filters may become any iterable besides a queryset.
        # That's still OK to return from get_queryset() though.
        filters = queryset

        name_search = self.request.query_params.get('name_search')
        if name_search is not None and name_search != '':
            filters = apply_name_search(filters, name_search)

        return filters


class FilterDetail(RetrieveUpdateDestroyAPIView):
    serializer_class = FilterSerializer
    lookup_url_kwarg = 'filter_id'

    def get_queryset(self):
        return Filter.objects.all()


class FilterRelationships(RelationshipView):
    """
    This endpoint would work as described here:
    https://jsonapi.org/format/#crud-updating-to-many-relationships
    For this model, the only candidate for related_field is
    outgoing_filter_implications.
    """
    lookup_url_kwarg = 'filter_id'
    queryset = Filter.objects
