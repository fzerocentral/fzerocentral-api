"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/dev/topics/http/urls/
"""
from django.urls import include, path


urlpatterns = [
    path('charts/', include('charts.urls', namespace='charts')),
    path('chart_groups/',
         include('chart_groups.urls', namespace='chart_groups')),
    path('chart_types/',
         include('chart_types.urls', namespace='chart_types')),
    path('chart_type_filter_groups/',
         include('chart_types.urls_ctfg',
                 namespace='chart_type_filter_groups')),
    path('filters/', include('filters.urls', namespace='filters')),
    path('filter_groups/',
         include('filter_groups.urls', namespace='filter_groups')),
    path('games/', include('games.urls', namespace='games')),
    path('ladders/', include('ladders.urls', namespace='ladders')),
    path('players/', include('players.urls', namespace='players')),
    path('records/', include('records.urls', namespace='records')),
]
