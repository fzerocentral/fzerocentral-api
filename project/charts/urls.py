from django.urls import path
from . import views


app_name = 'charts'

urlpatterns = [
    path('', views.ChartIndex.as_view(), name="index"),
    path('<int:chart_id>/', views.ChartDetail.as_view(), name="detail"),

    path(
        '<int:chart_id>/ranking/',
        views.ChartRanking.as_view(), name="ranking"),
    path(
        '<int:chart_id>/other_records/',
        views.ChartOtherRecords.as_view(), name="other_records"),
    path(
        '<int:chart_id>/record_history/',
        views.ChartRecordHistory.as_view(), name="record_history"),
]
