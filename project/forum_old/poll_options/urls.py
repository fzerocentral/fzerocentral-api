from django.urls import path
from . import views


app_name = 'forum_old_poll_options'

urlpatterns = [
    path('', views.PollOptionIndex.as_view(), name="index"),
]
