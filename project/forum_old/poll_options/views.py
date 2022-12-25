from rest_framework.generics import ListAPIView

from core.utils import filter_queryset_by_param
from .models import PollOption
from .serializers import PollOptionSerializer


class PollOptionIndex(ListAPIView):
    serializer_class = PollOptionSerializer

    def get_queryset(self):
        queryset = PollOption.objects.all()

        queryset = filter_queryset_by_param(
            self.request, 'poll_id', queryset, 'poll')

        queryset = queryset.order_by('option_number')
        return queryset
