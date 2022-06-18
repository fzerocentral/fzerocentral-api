from django.urls import path
from . import views


app_name = 'forum_old_posts'

urlpatterns = [
    path('', views.PostIndex.as_view(), name="index"),
    path('<int:post_id>/', views.PostDetail.as_view(), name="detail"),
]
