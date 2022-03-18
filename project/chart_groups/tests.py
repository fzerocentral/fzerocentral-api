from unittest import skip

from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from charts.models import Chart
from chart_types.models import ChartType
from games.models import Game
from .models import ChartGroup


class IndexTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.game = Game(name="F-Zero")
        cls.game.save()
        ct1 = ChartType(
            name="CT1", game=cls.game, format_spec=[], order_ascending=True)
        ct1.save()
        cls.cg_kl = ChartGroup(
            name="Knight League", order_in_parent=1, game=cls.game)
        cls.cg_kl.save()
        cls.cg_ql = ChartGroup(
            name="Queen League", order_in_parent=2, game=cls.game)
        cls.cg_ql.save()
        cls.cg_mc1 = ChartGroup(
            name="Mute City I", order_in_parent=1, game=cls.game,
            parent_group=cls.cg_kl)
        cls.cg_mc1.save()
        cls.chart_mc1c = Chart(
            name="Course Time", order_in_group=1, chart_group=cls.cg_mc1,
            chart_type=ct1)
        cls.chart_mc1c.save()

        game_2 = Game(name="F-Zero: Maximum Velocity")
        game_2.save()
        ChartGroup(name="Pawn Cup", order_in_parent=1, game=game_2).save()

    def test_filter_by_game(self):
        client = APIClient()
        response = client.get(
            reverse('chart_groups:index'), dict(game_id=self.game.id))
        self.assertEqual(response.status_code, 200)

        results = response.data['results']
        self.assertEqual(len(results), 3)
        self.assertDictEqual(
            results[0],
            dict(id=self.cg_kl.id, name="Knight League",
                 order_in_parent=1, charts=[],
                 # Related objects still have types, and string IDs.
                 child_groups=[
                     dict(type='chart-groups', id=str(self.cg_mc1.id))]))
        self.assertDictEqual(
            results[1],
            dict(id=self.cg_ql.id, name="Queen League",
                 order_in_parent=2, charts=[], child_groups=[]))
        self.assertDictEqual(
            results[2],
            dict(id=self.cg_mc1.id, name="Mute City I",
                 order_in_parent=1, child_groups=[], charts=[
                     dict(type='charts', id=str(self.chart_mc1c.id))]))

    def test_filter_by_game_and_parent(self):
        client = APIClient()
        response = client.get(
            reverse('chart_groups:index'),
            dict(game_id=self.game.id, parent_group_id=self.cg_kl.id))
        self.assertEqual(response.status_code, 200)

        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "Mute City I")

    def test_filter_by_game_and_null_parent(self):
        client = APIClient()
        response = client.get(
            reverse('chart_groups:index'),
            dict(game_id=self.game.id, parent_group_id=''))
        self.assertEqual(response.status_code, 200)

        results = response.data['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['name'], "Knight League")
        self.assertEqual(results[1]['name'], "Queen League")


# TODO: Look into getting a game's chart hierarchy in O(1) queries, and then
# un-skip this test. The problem at this time of writing is that the way the
# chart hierarchy is built is not at all conducive to using Django's
# queryset-based prefetching.
@skip
class IndexQueryCountTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.game = Game(name="Game")
        cls.game.save()
        ct1 = ChartType(
            name="CT1", game=cls.game, format_spec=[], order_ascending=True)
        ct1.save()

        # Make a chart group hierarchy with breadth and depth of at least 5.
        # And add about as many charts, some top level, some nested.

        for n in range(1, 5+1):
            cg = ChartGroup(
                name=f"Top level group {n}", order_in_parent=n, game=cls.game)
            cg.save()
            chart = Chart(
                chart_group=cg, name=f"Chart {cg.id}", order_in_group=1,
                chart_type=ct1)
            chart.save()

        cg = ChartGroup(
            name=f"Top level group 6", order_in_parent=6, game=cls.game)
        cg.save()
        prev_cg = cg
        for n in range(1, 5+1):
            cg = ChartGroup(
                name=f"Nested group {n}", order_in_parent=1,
                parent_group=prev_cg, game=cls.game)
            cg.save()
            prev_cg = cg
        for n in range(1, 5+1):
            chart = Chart(
                chart_group=cg, name=f"Nested chart {cg.id}", order_in_group=n,
                chart_type=ct1)
            chart.save()

    def test_query_count(self):
        with self.assertNumQueries(3):
            client = APIClient()
            response = client.get(
                reverse('chart_groups:index'),
                dict(game_id=self.game.id, parent_group_id=''))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.data['results']), 6)


class DetailTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.game = Game(name="F-Zero")
        cls.game.save()
        ct1 = ChartType(
            name="CT1", game=cls.game, format_spec=[], order_ascending=True)
        ct1.save()
        cls.cg_kl = ChartGroup(
            name="Knight League", order_in_parent=1, game=cls.game)
        cls.cg_kl.save()
        cls.cg_mc1 = ChartGroup(
            name="Mute City I", order_in_parent=1, game=cls.game,
            parent_group=cls.cg_kl)
        cls.cg_mc1.save()
        cls.chart_mc1c = Chart(
            name="Course Time", order_in_group=1, chart_group=cls.cg_mc1,
            chart_type=ct1)
        cls.chart_mc1c.save()

    def test(self):
        client = APIClient()
        response = client.get(
            reverse('chart_groups:detail', args=[self.cg_mc1.id]))
        self.assertEqual(response.status_code, 200)

        self.assertDictEqual(
            response.data,
            dict(id=self.cg_mc1.id, name="Mute City I", order_in_parent=1,
                 show_charts_together=False,
                 parent_group=dict(type='chart-groups', id=str(self.cg_kl.id)),
                 game=dict(type='games', id=str(self.game.id)),
                 charts=[
                     dict(type='charts', id=str(self.chart_mc1c.id))]))

    def test_nonexistent(self):
        group_id = self.cg_mc1.id
        self.cg_mc1.delete()

        client = APIClient()
        response = client.get(reverse('chart_groups:detail', args=[group_id]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data[0]['code'], 'not_found')
