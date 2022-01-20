from django.urls import path
from . import views


app_name = 'players'

urlpatterns = [
    path('', views.PlayerIndex.as_view(), name="index"),
    path('<int:player_id>/', views.PlayerDetail.as_view(), name="detail"),
]
