from django.urls import path
from . import views


app_name = 'forum_old_forums'

urlpatterns = [
    path('', views.ForumIndex.as_view(), name="index"),
    path('<int:forum_id>/', views.ForumDetail.as_view(), name="detail"),
]
