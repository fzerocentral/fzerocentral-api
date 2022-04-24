from rest_framework.generics import (
    ListCreateAPIView, RetrieveUpdateDestroyAPIView)
from rest_framework_json_api.views import RelationshipView

from core.utils import filter_queryset_by_param
from ladders.models import Ladder
from .models import Filter
from .serializers import FilterSerializer
from .utils import apply_name_search, FilterSpec


class FilterIndex(ListCreateAPIView):
    serializer_class = FilterSerializer

    def get_queryset(self):
        queryset = Filter.objects.all().order_by('name')

        # Comma separated IDs like 1,3,9,24
        filter_ids_str = self.request.query_params.get('filter_ids')
        if filter_ids_str is not None and filter_ids_str != '':
            queryset = queryset.filter(id__in=filter_ids_str.split(','))

        queryset = filter_queryset_by_param(
            self.request, 'filter_group_id',
            queryset, 'filter_group')

        queryset = filter_queryset_by_param(
            self.request, 'usage_type',
            queryset, 'usage_type')

        queryset = filter_queryset_by_param(
            self.request, 'implies_filter_id',
            queryset, 'outgoing_filter_implications')

        queryset = filter_queryset_by_param(
            self.request, 'implied_by_filter_id',
            queryset, 'incoming_filter_implications')

        ladder_id = self.request.query_params.get('ladder_id')
        if ladder_id is not None:
            ladder = Ladder.objects.get(id=ladder_id)
            filter_spec = FilterSpec(ladder.filter_spec)
            filter_ids = [item['filter_id'] for item in filter_spec.items]
            queryset = queryset.filter(id__in=filter_ids)

        name_search = self.request.query_params.get('name_search')
        if name_search is not None and name_search != '':
            queryset = apply_name_search(queryset, name_search)

        return queryset


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
