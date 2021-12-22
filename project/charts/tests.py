from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from chart_groups.models import ChartGroup
from games.models import Game
from .models import Chart


class IndexTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.game = Game(name="BS F-Zero Grand Prix 2")
        cls.game.save()
        cls.cg_mc4 = ChartGroup(
            name="Mute City IV", order_in_parent=1, game=cls.game)
        cls.cg_mc4.save()
        cls.cg_bb2 = ChartGroup(
            name="Big Blue II", order_in_parent=2, game=cls.game)
        cls.cg_bb2.save()

        cls.chart_mc4c = Chart(
            name="Course Time", order_in_group=1, chart_group=cls.cg_mc4)
        cls.chart_mc4c.save()
        cls.chart_mc4l = Chart(
            name="Lap Time", order_in_group=2, chart_group=cls.cg_mc4)
        cls.chart_mc4l.save()
        cls.chart_bb2c = Chart(
            name="Course Time", order_in_group=1, chart_group=cls.cg_bb2)
        cls.chart_bb2c.save()

    def test_filter_by_chart_group(self):
        client = APIClient()
        response = client.get(
            reverse('charts:index'), dict(chart_group_id=self.cg_mc4.id))
        self.assertEqual(response.status_code, 200)

        results = response.data['results']
        self.assertEqual(len(results), 2)
        self.assertDictEqual(
            results[0],
            dict(id=self.chart_mc4c.id, name="Course Time", order_in_group=1,
                 chart_group=dict(type='chart-groups', id=str(self.cg_mc4.id))))
        self.assertDictEqual(
            results[1],
            dict(id=self.chart_mc4l.id, name="Lap Time", order_in_group=2,
                 chart_group=dict(type='chart-groups', id=str(self.cg_mc4.id))))


class DetailTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.game = Game(name="BS F-Zero Grand Prix 2")
        cls.game.save()
        cls.cg_mc4 = ChartGroup(
            name="Mute City IV", order_in_parent=1, game=cls.game)
        cls.cg_mc4.save()
        cls.chart_mc4c = Chart(
            name="Course Time", order_in_group=1, chart_group=cls.cg_mc4)
        cls.chart_mc4c.save()

    def test(self):
        client = APIClient()
        response = client.get(
            reverse('charts:detail', args=[self.chart_mc4c.id]))
        self.assertEqual(response.status_code, 200)

        self.assertDictEqual(
            response.data,
            dict(id=self.chart_mc4c.id, name="Course Time", order_in_group=1,
                 chart_group=dict(type='chart-groups', id=str(self.cg_mc4.id))))

    def test_nonexistent(self):
        chart_id = self.chart_mc4c.id
        self.chart_mc4c.delete()

        client = APIClient()
        response = client.get(reverse('charts:detail', args=[chart_id]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data[0]['code'], 'not_found')
