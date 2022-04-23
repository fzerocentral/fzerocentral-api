from django.urls import path
from . import views


app_name = 'ladders'

urlpatterns = [
    path('', views.LadderIndex.as_view(), name="index"),
    path('<int:ladder_id>/', views.LadderDetail.as_view(), name="detail"),

    path(
        '<int:ladder_id>/ranking/',
        views.LadderRanking.as_view(), name="ranking"),
]
