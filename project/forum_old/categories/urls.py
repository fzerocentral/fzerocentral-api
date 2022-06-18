from django.urls import path
from . import views


app_name = 'forum_old_categories'

urlpatterns = [
    path('', views.CategoryIndex.as_view(), name="index"),
    path('<int:category_id>/', views.CategoryDetail.as_view(), name="detail"),
]
