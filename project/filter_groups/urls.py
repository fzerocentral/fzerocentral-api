from django.urls import path
from . import views


app_name = 'filter_groups'

urlpatterns = [
    path('', views.FilterGroupIndex.as_view(), name="index"),
    path('<int:group_id>/', views.FilterGroupDetail.as_view(), name="detail"),
]
