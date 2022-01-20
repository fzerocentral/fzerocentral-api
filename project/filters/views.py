import re

from rest_framework.generics import (
    ListCreateAPIView, RetrieveUpdateDestroyAPIView)
from rest_framework_json_api.views import RelationshipView

from .models import Filter
from .serializers import FilterSerializer


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

        name_search = self.request.query_params.get('name_search')
        if name_search is not None:
            # Remove all chars besides letters, numbers, and spaces
            search_term = re.sub(r'[^\w\s]', '', name_search)
            # Case-insensitive 'contains this string' test on the filter name
            queryset = queryset.filter(name__icontains=search_term)

        implies_filter_id = self.request.query_params.get('implies_filter_id')
        if implies_filter_id is not None:
            queryset = queryset.filter(
                outgoing_filter_implications=implies_filter_id)

        implied_by_filter_id = self.request.query_params.get(
            'implied_by_filter_id')
        if implied_by_filter_id is not None:
            queryset = queryset.filter(
                incoming_filter_implications=implied_by_filter_id)

        return queryset


class FilterDetail(RetrieveUpdateDestroyAPIView):
    serializer_class = FilterSerializer
    lookup_url_kwarg = 'filter_id'

    def get_queryset(self):
        return Filter.objects.all()


class FilterRelationships(RelationshipView):
    # The URL's related_field can only be outgoing_filter_implications.
    # See https://jsonapi.org/format/#crud-updating-to-many-relationships
    lookup_url_kwarg = 'filter_id'
    queryset = Filter.objects