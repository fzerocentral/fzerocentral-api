from django.urls import path
from . import views


app_name = 'forum_old_polls'

urlpatterns = [
    path('<int:poll_id>/', views.PollDetail.as_view(), name="detail"),
]
