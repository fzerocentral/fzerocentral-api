from django.db.models import Min
from rest_framework.generics import (
    ListCreateAPIView, RetrieveUpdateDestroyAPIView)

from chart_types.models import CTFG
from .models import FilterGroup
from .serializers import FilterGroupSerializer


class FilterGroupIndex(ListCreateAPIView):
    serializer_class = FilterGroupSerializer

    def get_queryset(self):
        queryset = FilterGroup.objects.all().order_by('name')

        game_id = self.request.query_params.get('game_id')
        if game_id is not None:
            queryset = queryset.filter(ctfg__chart_type__game=game_id)

        chart_type_id = self.request.query_params.get('chart_type_id')
        if chart_type_id == '':
            # Get orphaned filter groups - not linked to any chart type.
            queryset = queryset.filter(ctfg=None)
        elif chart_type_id is not None:
            # Order the filter groups by the order field in the
            # intermediate model 'CTFG'. The way to do this (while keeping
            # results as querysets, not lists) is pretty complex:
            # https://www.petrounias.org/articles/2010/02/06/ordering-on-a-field-in-the-through-model-of-a-recursive-manytomany-relation-in-django/
            ctfgs = CTFG.objects.filter(chart_type=chart_type_id)
            queryset = queryset.filter(
                ctfg__in=ctfgs).annotate(
                    ctfg_order=Min(
                        'ctfg__order_in_chart_type')).order_by(
                            'ctfg_order').distinct()

        return queryset


class FilterGroupDetail(RetrieveUpdateDestroyAPIView):
    serializer_class = FilterGroupSerializer
    lookup_url_kwarg = 'group_id'

    def get_queryset(self):
        return FilterGroup.objects.all()
