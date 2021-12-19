import json

from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from .models import Game


class IndexTest(TestCase):

    def test(self):
        game_1 = Game(name="F-Zero")
        game_1.save()
        game_2 = Game(name="BS F-Zero Grand Prix 2")
        game_2.save()

        client = Client()
        response = client.get(reverse('games:index'))
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            json.loads(response.content)['data'],
            [dict(id=game_1.pk, name="F-Zero"),
             dict(id=game_2.pk, name="BS F-Zero Grand Prix 2")])


class DetailTest(TestCase):

    def test(self):
        game = Game(name="F-Zero")
        game.save()

        client = Client()
        response = client.get(reverse('games:detail', args=[game.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            json.loads(response.content)['data'],
            dict(id=game.pk, name="F-Zero"))

    def test_nonexistent(self):
        # Guarantee a nonexistent PK by creating a game, then deleting it.
        game = Game(name="F-Zero")
        game.save()
        game_pk = game.pk
        game.delete()

        client = Client()
        response = client.get(reverse('games:detail', args=[game_pk]))
        self.assertEqual(response.status_code, 404)
