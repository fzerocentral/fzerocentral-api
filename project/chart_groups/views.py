from rest_framework.generics import ListAPIView, RetrieveAPIView

from .models import ChartGroup
from .serializers import ChartGroupSerializer, ChartGroupHierarchySerializer


class ChartGroupIndex(ListAPIView):
    serializer_class = ChartGroupHierarchySerializer

    def get_queryset(self):
        queryset = ChartGroup.objects.all().order_by('id')

        game_id = self.request.query_params.get('game_id')
        if game_id is not None:
            queryset = queryset.filter(game=game_id)

        parent_group_id = self.request.query_params.get('parent_group_id')
        if parent_group_id is not None:
            if parent_group_id == '':
                queryset = queryset.filter(parent_group__isnull=True)
            else:
                queryset = queryset.filter(parent_group=parent_group_id)
            queryset = queryset.order_by('order_in_parent')

        return queryset


class ChartGroupDetail(RetrieveAPIView):

    def get_queryset(self):
        return ChartGroup.objects.all()
    serializer_class = ChartGroupSerializer
    lookup_url_kwarg = 'group_id'
