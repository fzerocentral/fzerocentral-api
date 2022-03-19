from django.urls import reverse
from rest_framework.test import APIClient


def create_fg(game, name, order=None):
    data = {
        'type': 'filter-groups',
        'attributes': {
            'name': name,
            'description': "Description here",
        },
        'relationships': {
            'game': {
                'data': {
                    'type': 'games',
                    'id': game.id,
                }
            },
        },
    }
    if order is not None:
        data['attributes']['order-in-game'] = order

    client = APIClient()
    response = client.post(
        reverse('filter_groups:index'), {'data': data})
    return response
