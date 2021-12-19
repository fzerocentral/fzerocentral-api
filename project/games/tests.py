import json

from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from .models import Game


class IndexTest(APITestCase):

    def test_content(self):
        game_1 = Game(name="F-Zero")
        game_1.save()
        game_2 = Game(name="BS F-Zero Grand Prix 2")
        game_2.save()

        client = APIClient()
        response = client.get(reverse('games:index'))
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            json.loads(response.content)['data'],
            [dict(type='games', id=str(game_2.pk),
                  attributes=dict(name="BS F-Zero Grand Prix 2")),
             dict(type='games', id=str(game_1.pk),
                  attributes=dict(name="F-Zero"))])


class DetailTest(APITestCase):

    def test_content(self):
        game = Game(name="F-Zero")
        game.save()

        client = APIClient()
        response = client.get(reverse('games:detail', args=[game.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            json.loads(response.content)['data'],
            dict(type='games', id=str(game.pk),
                 attributes=dict(name="F-Zero")))

    def test_nonexistent(self):
        # Guarantee a nonexistent PK by creating a game, then deleting it.
        game = Game(name="F-Zero")
        game.save()
        game_pk = game.pk
        game.delete()

        client = APIClient()
        response = client.get(reverse('games:detail', args=[game_pk]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data[0]['code'], 'not_found')
