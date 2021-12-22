from django.urls import path
from . import views


app_name = 'charts'

urlpatterns = [
    path('', views.ChartIndex.as_view(), name="index"),
    path('<int:chart_id>/', views.ChartDetail.as_view(), name="detail"),
]
