from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from charts.models import Chart
from chart_groups.models import ChartGroup
from chart_types.models import ChartType
from games.models import Game
from ..models import FilterGroup
from .utils import create_fg


class FilterGroupIndexTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.game = Game(name="G")
        cls.game.save()
        game_2 = Game(name="G")
        game_2.save()
        cg1 = ChartGroup(name="CG1", game=cls.game, order_in_parent=1)
        cg1.save()
        cls.ct1 = ChartType(
            name="CT1", game=cls.game, format_spec=[], order_ascending=True)
        cls.ct1.save()
        cls.ct2 = ChartType(
            name="CT2", game=cls.game, format_spec=[], order_ascending=True)
        cls.ct2.save()
        cls.c1 = Chart(
            name="C1", chart_group=cg1, order_in_group=1, chart_type=cls.ct1)
        cls.c1.save()
        cls.c2 = Chart(
            name="C2", chart_group=cg1, order_in_group=2, chart_type=cls.ct2)
        cls.c2.save()

        # Add FGs to game 1 specifying a different order from alphabetical
        # or FG ID, so we can tell the order field is respected.
        cls.fg1 = FilterGroup(name="FG1", game=cls.game, order_in_game=2)
        cls.fg1.save()
        cls.fg2 = FilterGroup(name="FG2", game=cls.game, order_in_game=1)
        cls.fg2.save()
        cls.fg3 = FilterGroup(name="FG3", game=cls.game, order_in_game=3)
        cls.fg3.save()
        cls.fg4 = FilterGroup(name="FG4", game=cls.game, order_in_game=4)
        cls.fg4.save()
        # Add one FG to game 2, so that we can tell we're only getting FGs
        # of game 1.
        cls.fg5 = FilterGroup(name="FG5", game=game_2, order_in_game=1)
        cls.fg5.save()

        # Don't link FG4, so we can tell we're only getting FGs of this CT.
        cls.ct1.filter_groups.add(cls.fg1, cls.fg2, cls.fg3)

    def test_filter_by_chart_type(self):
        client = APIClient()
        response = client.get(
            reverse('filter_groups:index'), dict(chart_type_id=self.ct1.id))
        self.assertEqual(response.status_code, 200)

        results = response.data['results']
        self.assertListEqual(
            [fg['name'] for fg in results], ["FG2", "FG1", "FG3"],
            "Should filter by chart type and respect order field")

    def test_filter_by_chart(self):
        client = APIClient()
        response = client.get(
            reverse('filter_groups:index'), dict(chart_id=self.c1.id))
        self.assertEqual(response.status_code, 200)

        results = response.data['results']
        self.assertListEqual(
            [fg['name'] for fg in results], ["FG2", "FG1", "FG3"],
            "Should filter by chart and respect order field")


class FilterGroupCreateTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.game = Game(name="G")
        cls.game.save()

    def test_insert_only_fg(self):
        response = create_fg(self.game, "FG1")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_insert_first_fg(self):
        """(new) 1"""
        fg1 = FilterGroup(
            game=self.game, name="FG1", description="Test", order_in_game=1)
        fg1.save()

        response = create_fg(self.game, "FG2", order=1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        fg1.refresh_from_db()
        self.assertEqual(fg1.order_in_game, 2)

    def test_insert_fg_beyond_minimum_order(self):
        response = create_fg(self.game, "FG1", order=0)
        self.assertEqual(response.data['order_in_game'], 1)

    def test_insert_last_fg(self):
        """1 (new)"""
        fg1 = FilterGroup(
            game=self.game, name="FG1", description="Test", order_in_game=1)
        fg1.save()

        response = create_fg(self.game, "FG2", order=2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        fg1.refresh_from_db()
        self.assertEqual(fg1.order_in_game, 1)

    def test_insert_fg_beyond_maximum_order(self):
        fg1 = FilterGroup(
            game=self.game, name="FG1", description="Test", order_in_game=1)
        fg1.save()

        response = create_fg(self.game, "FG2", order=3)
        self.assertEqual(response.data['order_in_game'], 2)

    def test_insert_middle_fg(self):
        """1 (new) 2 3"""
        fg1 = FilterGroup(
            game=self.game, name="FG1", description="Test", order_in_game=1)
        fg1.save()
        fg2 = FilterGroup(
            game=self.game, name="FG2", description="Test", order_in_game=2)
        fg2.save()
        fg3 = FilterGroup(
            game=self.game, name="FG3", description="Test", order_in_game=3)
        fg3.save()

        create_fg(self.game, "FG4", order=2)

        fg1.refresh_from_db()
        self.assertEqual(fg1.order_in_game, 1)
        fg2.refresh_from_db()
        self.assertEqual(fg2.order_in_game, 3)
        fg3.refresh_from_db()
        self.assertEqual(fg3.order_in_game, 4)


class FilterGroupPatchAndDeleteTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.game = Game(name="G")
        cls.game.save()
        cls.fg1 = FilterGroup(
            game=cls.game, name="FG1", description="Test", order_in_game=1)
        cls.fg1.save()
        cls.fg2 = FilterGroup(
            game=cls.game, name="FG2", description="Test", order_in_game=2)
        cls.fg2.save()
        cls.fg3 = FilterGroup(
            game=cls.game, name="FG3", description="Test", order_in_game=3)
        cls.fg3.save()
        cls.fg4 = FilterGroup(
            game=cls.game, name="FG4", description="Test", order_in_game=4)
        cls.fg4.save()
        cls.fg5 = FilterGroup(
            game=cls.game, name="FG5", description="Test", order_in_game=5)
        cls.fg5.save()

    @staticmethod
    def reorder_fg(fg, order):
        data = {
            'id': fg.id,
            'type': 'filter-groups',
            'attributes': {
                'order-in-game': order,
            },
        }

        client = APIClient()
        response = client.patch(
            reverse('filter_groups:detail', args=[fg.id]),
            {'data': data})
        return response

    @staticmethod
    def delete_fg(fg):
        client = APIClient()
        response = client.delete(
            reverse('filter_groups:detail', args=[fg.id]))
        return response

    def assert_full_ordering(self, *expected_ordering):
        self.game.refresh_from_db()
        actual_ordering = []
        for fg in self.game.filtergroup_set.order_by('order_in_game'):
            if fg.id == self.fg1.id:
                actual_ordering.append(1)
            elif fg.id == self.fg2.id:
                actual_ordering.append(2)
            elif fg.id == self.fg3.id:
                actual_ordering.append(3)
            elif fg.id == self.fg4.id:
                actual_ordering.append(4)
            elif fg.id == self.fg5.id:
                actual_ordering.append(5)
        self.assertListEqual(actual_ordering, list(expected_ordering))

    def test_reorder_forward(self):
        self.reorder_fg(self.fg2, 4)
        self.assert_full_ordering(1, 3, 4, 2, 5)

    def test_reorder_backward(self):
        self.reorder_fg(self.fg4, 2)
        self.assert_full_ordering(1, 4, 2, 3, 5)

    def test_reorder_beyond_minimum_order(self):
        self.reorder_fg(self.fg3, 0)
        self.assert_full_ordering(3, 1, 2, 4, 5)

    def test_reorder_beyond_maximum_order(self):
        self.reorder_fg(self.fg3, 6)
        self.assert_full_ordering(1, 2, 4, 5, 3)

    def test_delete_first(self):
        self.delete_fg(self.fg1)
        self.assert_full_ordering(2, 3, 4, 5)

    def test_delete_middle(self):
        self.delete_fg(self.fg3)
        self.assert_full_ordering(1, 2, 4, 5)

    def test_delete_last(self):
        self.delete_fg(self.fg5)
        self.assert_full_ordering(1, 2, 3, 4)
