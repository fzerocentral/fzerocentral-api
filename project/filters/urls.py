from django.urls import path
from . import views


app_name = 'filters'

urlpatterns = [
    path('', views.FilterIndex.as_view(), name="index"),
    path('<int:filter_id>/', views.FilterDetail.as_view(), name="detail"),

    path(
        '<int:filter_id>/relationships/<related_field>/',
        views.FilterRelationships.as_view(), name="relationships"),
]
