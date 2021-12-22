import json

from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from .models import Game


class IndexTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.game_1 = Game(name="F-Zero")
        cls.game_1.save()
        cls.game_2 = Game(name="BS F-Zero Grand Prix 2")
        cls.game_2.save()

    def test_content(self):
        client = APIClient()
        response = client.get(reverse('games:index'))
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            json.loads(response.content)['data'],
            [dict(type='games', id=str(self.game_2.id),
                  attributes=dict(name="BS F-Zero Grand Prix 2")),
             dict(type='games', id=str(self.game_1.id),
                  attributes=dict(name="F-Zero"))])

    def test_data(self):
        client = APIClient()
        response = client.get(reverse('games:index'))
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            response.data['results'],
            [dict(id=self.game_2.id,
                  name="BS F-Zero Grand Prix 2"),
             dict(id=self.game_1.id,
                  name="F-Zero")])


class DetailTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.game = Game(name="F-Zero")
        cls.game.save()

    def test_content(self):
        client = APIClient()
        response = client.get(reverse('games:detail', args=[self.game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            json.loads(response.content)['data'],
            dict(type='games', id=str(self.game.id),
                 attributes=dict(name="F-Zero")))

    def test_data(self):
        client = APIClient()
        response = client.get(reverse('games:detail', args=[self.game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.data,
            dict(id=self.game.id, name="F-Zero"))

    def test_nonexistent(self):
        # Guarantee a nonexistent ID by creating a game, then deleting it.
        game_id = self.game.id
        self.game.delete()

        client = APIClient()
        response = client.get(reverse('games:detail', args=[game_id]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data[0]['code'], 'not_found')
