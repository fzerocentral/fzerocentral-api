from django.urls import path
from . import views


app_name = 'records'

urlpatterns = [
    path('', views.RecordIndex.as_view(), name="index"),
    path('<int:record_id>/', views.RecordDetail.as_view(), name="detail"),
]
