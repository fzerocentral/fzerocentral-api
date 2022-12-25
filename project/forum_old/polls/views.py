from rest_framework.generics import RetrieveAPIView

from .models import Poll
from .serializers import PollSerializer


class PollDetail(RetrieveAPIView):
    serializer_class = PollSerializer
    lookup_url_kwarg = 'poll_id'

    def get_queryset(self):
        return Poll.objects.all()
