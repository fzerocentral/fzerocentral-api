from django.urls import path
from . import views


app_name = 'chart_types'

urlpatterns = [
    path('', views.CTFGIndex.as_view(), name="index"),
    path('<int:ctfg_id>/', views.CTFGDetail.as_view(), name="detail"),
]
