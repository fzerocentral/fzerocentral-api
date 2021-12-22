"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/dev/topics/http/urls/
"""
from django.urls import include, path


urlpatterns = [
    path('charts/', include('charts.urls', namespace='charts')),
    path('chart_groups/',
         include('chart_groups.urls', namespace='chart_groups')),
    path('games/', include('games.urls', namespace='games')),
]
