from django.urls import reverse
from rest_framework.test import APIClient


def link_ct_and_fg(chart_type, filter_group):
    filter_groups = set(chart_type.filter_groups.all())
    filter_groups.add(filter_group)
    filter_groups_data = [
        dict(id=fg.id, type='filter-groups') for fg in filter_groups]
    data = {
        'type': 'chart-types',
        'id': chart_type.id,
        'relationships': {
            'filter-groups': {
                'data': filter_groups_data
            },
        },
    }

    client = APIClient()
    response = client.patch(
        reverse('chart_types:detail', args=[chart_type.id]),
        {'data': data})
    return response
