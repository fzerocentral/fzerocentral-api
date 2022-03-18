from django.urls import reverse
from rest_framework.test import APIClient


def create_ctfg(ct, fg, order=None):
    data = {
        'type': 'chart-type-filter-groups',
        'relationships': {
            'chart-type': {
                'data': {
                    'type': 'chart-types',
                    'id': ct.id,
                }
            },
            'filter-group': {
                'data': {
                    'type': 'filter-groups',
                    'id': fg.id,
                }
            },
        },
    }
    if order is not None:
        data['attributes'] = {'order-in-chart-type': order}

    client = APIClient()
    response = client.post(
        reverse('chart_type_filter_groups:index'), {'data': data})
    return response
