from rest_framework.generics import (
    ListCreateAPIView, RetrieveUpdateDestroyAPIView)

from filters.utils import apply_filter_spec, FilterSpec
from .models import Record
from .serializers import RecordSerializer
from .utils import sort_records_by_value


class RecordIndex(ListCreateAPIView):
    serializer_class = RecordSerializer

    def get_queryset(self):
        queryset = Record.objects.all()

        # Filtering

        chart_id = self.request.query_params.get('chart_id')
        if chart_id is not None:
            queryset = queryset.filter(chart=chart_id)

        player_id = self.request.query_params.get('player_id')
        if player_id is not None:
            queryset = queryset.filter(player=player_id)

        filter_spec = self.request.query_params.get('filters')
        if filter_spec is not None and filter_spec != '':
            queryset = apply_filter_spec(queryset, FilterSpec(filter_spec))

        # Sorting

        sort_method = self.request.query_params.get('sort', 'date_submitted')
        if sort_method == 'date_submitted':
            # Latest date first. Date granularity is limited, so ties are
            # possible. Therefore, we do a secondary ordering by record ID,
            # which makes the order repeatable, and also orders by creation
            # time in most cases.
            queryset = queryset.order_by('-date_created', '-id')
        elif sort_method == 'date_achieved':
            # Latest date first. The secondary ordering by record ID makes the
            # result order repeatable.
            queryset = queryset.order_by('-date_achieved', '-id')
        elif sort_method == 'value':
            queryset = sort_records_by_value(queryset, chart_id)
        else:
            raise ValueError(f"Unrecognized sort method: {sort_method}")

        return queryset


class RecordDetail(RetrieveUpdateDestroyAPIView):
    serializer_class = RecordSerializer
    lookup_url_kwarg = 'record_id'

    def get_queryset(self):
        return Record.objects.all()
