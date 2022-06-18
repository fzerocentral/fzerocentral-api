from django.urls import path
from . import views


app_name = 'forum_old_topics'

urlpatterns = [
    path('', views.TopicIndex.as_view(), name="index"),
    path('<int:topic_id>/', views.TopicDetail.as_view(), name="detail"),
]
