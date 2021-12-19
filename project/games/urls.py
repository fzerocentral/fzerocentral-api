from django.urls import path
from . import views


app_name = 'games'

urlpatterns = [
    path('', views.GameIndex.as_view(), name="index"),
    path('<int:game_pk>/', views.GameDetail.as_view(), name="detail"),
]
