from django.db.models import F
from rest_framework.generics import (
    ListAPIView, ListCreateAPIView,
    RetrieveAPIView, RetrieveUpdateDestroyAPIView)

from .models import ChartType, CTFG
from .serializers import ChartTypeSerializer, CTFGSerializer


class ChartTypeIndex(ListAPIView):
    serializer_class = ChartTypeSerializer

    def get_queryset(self):
        queryset = ChartType.objects.all().order_by('name')

        game_id = self.request.query_params.get('game_id')
        if game_id is not None:
            queryset = queryset.filter(game=game_id)

        filter_group_id = self.request.query_params.get('filter_group_id')
        if filter_group_id is not None:
            queryset = queryset.filter(filter_groups=filter_group_id)

        return queryset


class ChartTypeDetail(RetrieveAPIView):
    serializer_class = ChartTypeSerializer
    lookup_url_kwarg = 'chart_type_id'

    def get_queryset(self):
        return ChartType.objects.all()


class CTFGIndex(ListCreateAPIView):
    serializer_class = CTFGSerializer

    def get_queryset(self):
        queryset = CTFG.objects.all().order_by('id')

        chart_type_id = self.request.query_params.get('chart_type_id')
        if chart_type_id is not None:
            queryset = queryset.filter(chart_type=chart_type_id).order_by(
                'order_in_chart_type')

        return queryset

    def create(self, request, *args, **kwargs):
        order_in_chart_type = request.data.get('order_in_chart_type')
        existing_ctfgs = CTFG.objects.filter(
            chart_type=request.data['chart_type']['id'])

        if order_in_chart_type is None:
            # By default, order at the end, after all existing CTFGs.
            order_in_chart_type = existing_ctfgs.count() + 1
        elif order_in_chart_type < 1:
            # Restrict the order to the accepted range.
            order_in_chart_type = 1
        elif order_in_chart_type > existing_ctfgs.count() + 1:
            # Restrict the order to the accepted range.
            order_in_chart_type = existing_ctfgs.count() + 1

        # Change other CTFGs' order as needed to accommodate the new CTFG. We
        # need to +1 the order of CTFGs coming after this one.
        later_ctfgs = existing_ctfgs.filter(
            order_in_chart_type__gte=order_in_chart_type)
        later_ctfgs.update(order_in_chart_type=F('order_in_chart_type')+1)

        # Then we insert the new CTFG.
        request.data['order_in_chart_type'] = order_in_chart_type
        return super().create(request, *args, **kwargs)


class CTFGDetail(RetrieveUpdateDestroyAPIView):
    serializer_class = CTFGSerializer
    lookup_url_kwarg = 'ctfg_id'

    def get_queryset(self):
        return CTFG.objects.all()

    def patch(self, request, *args, **kwargs):
        ctfg = self.get_object()
        ct_ctfgs = CTFG.objects.filter(chart_type=ctfg.chart_type)
        new_order = request.data.get('order_in_chart_type')

        if new_order is not None:
            old_order = ctfg.order_in_chart_type

            # Restrict the order to the accepted range.
            if new_order < 1:
                new_order = 1
            elif new_order > ct_ctfgs.count():
                new_order = ct_ctfgs.count()
            request.data['order_in_chart_type'] = new_order

            # Inc/dec the order of CTFGs between this CTFG's old and new order,
            # then set this CTFG to the desired order.
            if old_order < new_order:
                # e.g. ABCDEF -> ABDEFC (moved C)
                # CTFGs in between the old and new positions move backward.
                affected_ctfgs = ct_ctfgs.filter(
                    order_in_chart_type__gt=old_order,
                    order_in_chart_type__lte=new_order)
                affected_ctfgs.update(
                    order_in_chart_type=F('order_in_chart_type')-1)
            elif new_order < old_order:
                # e.g. ABCDEF -> ABFCDE (moved F)
                # CTFGs in between the old and new positions move forward.
                affected_ctfgs = ct_ctfgs.filter(
                    order_in_chart_type__lt=old_order,
                    order_in_chart_type__gte=new_order)
                affected_ctfgs.update(
                    order_in_chart_type=F('order_in_chart_type')+1)

        return super().patch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        # Decrement the order of CTFGs coming after
        # this CTFG, then delete this CTFG.
        ctfg = self.get_object()
        ct_ctfgs = CTFG.objects.filter(chart_type=ctfg.chart_type)
        affected_ctfgs = ct_ctfgs.filter(
            order_in_chart_type__gt=ctfg.order_in_chart_type)
        affected_ctfgs.update(
            order_in_chart_type=F('order_in_chart_type')-1)

        return super().delete(request, *args, **kwargs)
