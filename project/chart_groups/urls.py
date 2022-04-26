from django.urls import path
from . import views


app_name = 'chart_groups'

urlpatterns = [
    path('', views.ChartGroupIndex.as_view(), name="index"),
    path('<int:group_id>/', views.ChartGroupDetail.as_view(), name="detail"),

    path(
        '<int:group_id>/hierarchy/',
        views.ChartGroupHierarchy.as_view(), name="hierarchy"),
]
