from django.urls import path
from . import views


app_name = 'chart_types'

urlpatterns = [
    path('', views.ChartTypeIndex.as_view(), name="index"),
    path('<int:chart_type_id>/', views.ChartTypeDetail.as_view(), name="detail"),
]
