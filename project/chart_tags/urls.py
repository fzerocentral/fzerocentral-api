from django.urls import path
from . import views


app_name = 'chart_tags'

urlpatterns = [
    path('', views.ChartTagIndex.as_view(), name="index"),
    path('<int:chart_tag_id>/', views.ChartTagDetail.as_view(), name="detail"),
]
