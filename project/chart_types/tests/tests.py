from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from filter_groups.models import FilterGroup
from games.models import Game
from ..models import ChartType, CTFG
from .utils import create_ctfg


class CTFGIndexTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.game = Game(name="G")
        cls.game.save()
        cls.ct1 = ChartType(
            name="CT1", game=cls.game, format_spec=[], order_ascending=True)
        cls.ct1.save()
        cls.fg1 = FilterGroup(name="FG1")
        cls.fg1.save()
        cls.fg2 = FilterGroup(name="FG2")
        cls.fg2.save()
        cls.fg3 = FilterGroup(name="FG3")
        cls.fg3.save()
        cls.fg4 = FilterGroup(name="FG4")
        cls.fg4.save()

    def test_insert_only_ctfg(self):
        response = create_ctfg(self.ct1, self.fg1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_insert_first_ctfg(self):
        """(new) 1"""
        ctfg1 = CTFG(
            chart_type=self.ct1, filter_group=self.fg1, order_in_chart_type=1)
        ctfg1.save()

        create_ctfg(self.ct1, self.fg2, order=1)

        ctfg1.refresh_from_db()
        self.assertEqual(ctfg1.order_in_chart_type, 2)

    def test_insert_ctfg_beyond_minimum_order(self):
        response = create_ctfg(self.ct1, self.fg1, order=0)
        self.assertEqual(response.data['order_in_chart_type'], 1)

    def test_insert_last_ctfg(self):
        """1 (new)"""
        ctfg1 = CTFG(
            chart_type=self.ct1, filter_group=self.fg1, order_in_chart_type=1)
        ctfg1.save()

        create_ctfg(self.ct1, self.fg2, order=2)

        ctfg1.refresh_from_db()
        self.assertEqual(ctfg1.order_in_chart_type, 1)

    def test_insert_ctfg_beyond_maximum_order(self):
        ctfg1 = CTFG(
            chart_type=self.ct1, filter_group=self.fg1, order_in_chart_type=1)
        ctfg1.save()

        response = create_ctfg(self.ct1, self.fg2, order=3)
        self.assertEqual(response.data['order_in_chart_type'], 2)

    def test_insert_middle_ctfg(self):
        """1 (new) 2 3"""
        ctfg1 = CTFG(
            chart_type=self.ct1, filter_group=self.fg1, order_in_chart_type=1)
        ctfg1.save()
        ctfg2 = CTFG(
            chart_type=self.ct1, filter_group=self.fg2, order_in_chart_type=2)
        ctfg2.save()
        ctfg3 = CTFG(
            chart_type=self.ct1, filter_group=self.fg3, order_in_chart_type=3)
        ctfg3.save()

        create_ctfg(self.ct1, self.fg4, order=2)

        ctfg1.refresh_from_db()
        self.assertEqual(ctfg1.order_in_chart_type, 1)
        ctfg2.refresh_from_db()
        self.assertEqual(ctfg2.order_in_chart_type, 3)
        ctfg3.refresh_from_db()
        self.assertEqual(ctfg3.order_in_chart_type, 4)


class CTFGDetailTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.game = Game(name="G")
        cls.game.save()
        cls.ct1 = ChartType(
            name="CT1", game=cls.game, format_spec=[], order_ascending=True)
        cls.ct1.save()
        cls.fg1 = FilterGroup(name="FG1")
        cls.fg1.save()
        cls.fg2 = FilterGroup(name="FG2")
        cls.fg2.save()
        cls.fg3 = FilterGroup(name="FG3")
        cls.fg3.save()
        cls.fg4 = FilterGroup(name="FG4")
        cls.fg4.save()
        cls.fg5 = FilterGroup(name="FG5")
        cls.fg5.save()
        cls.ctfg1 = CTFG(
            chart_type=cls.ct1, filter_group=cls.fg1, order_in_chart_type=1)
        cls.ctfg1.save()
        cls.ctfg2 = CTFG(
            chart_type=cls.ct1, filter_group=cls.fg2, order_in_chart_type=2)
        cls.ctfg2.save()
        cls.ctfg3 = CTFG(
            chart_type=cls.ct1, filter_group=cls.fg3, order_in_chart_type=3)
        cls.ctfg3.save()
        cls.ctfg4 = CTFG(
            chart_type=cls.ct1, filter_group=cls.fg4, order_in_chart_type=4)
        cls.ctfg4.save()
        cls.ctfg5 = CTFG(
            chart_type=cls.ct1, filter_group=cls.fg5, order_in_chart_type=5)
        cls.ctfg5.save()

    @staticmethod
    def reorder_ctfg(ctfg, order):
        data = {
            'id': ctfg.id,
            'type': 'chart-type-filter-groups',
            'attributes': {
                'order-in-chart-type': order,
            },
            'relationships': {
                'chart-type': {
                    'data': {
                        'type': 'chart-types',
                        'id': ctfg.chart_type_id,
                    }
                },
                'filter-group': {
                    'data': {
                        'type': 'filter-groups',
                        'id': ctfg.filter_group_id,
                    }
                },
            },
        }

        client = APIClient()
        response = client.patch(
            reverse('chart_type_filter_groups:detail', args=[ctfg.id]),
            {'data': data})
        return response

    @staticmethod
    def delete_ctfg(ctfg):
        client = APIClient()
        response = client.delete(
            reverse('chart_type_filter_groups:detail', args=[ctfg.id]))
        return response

    def assert_full_ordering(self, *expected_ordering):
        self.ct1.refresh_from_db()
        actual_ordering = []
        for ctfg in self.ct1.filter_groups.order_by(
                'ctfg__order_in_chart_type'):
            match ctfg.id:
                case self.ctfg1.id:
                    actual_ordering.append(1)
                case self.ctfg2.id:
                    actual_ordering.append(2)
                case self.ctfg3.id:
                    actual_ordering.append(3)
                case self.ctfg4.id:
                    actual_ordering.append(4)
                case self.ctfg5.id:
                    actual_ordering.append(5)
        self.assertListEqual(actual_ordering, list(expected_ordering))

    def test_reorder_forward(self):
        self.reorder_ctfg(self.ctfg2, 4)
        self.assert_full_ordering(1, 3, 4, 2, 5)

    def test_reorder_backward(self):
        self.reorder_ctfg(self.ctfg4, 2)
        self.assert_full_ordering(1, 4, 2, 3, 5)

    def test_reorder_beyond_minimum_order(self):
        self.reorder_ctfg(self.ctfg3, 0)
        self.assert_full_ordering(3, 1, 2, 4, 5)

    def test_reorder_beyond_maximum_order(self):
        self.reorder_ctfg(self.ctfg3, 6)
        self.assert_full_ordering(1, 2, 4, 5, 3)

    def test_delete_first(self):
        self.delete_ctfg(self.ctfg1)
        self.assert_full_ordering(2, 3, 4, 5)

    def test_delete_middle(self):
        self.delete_ctfg(self.ctfg3)
        self.assert_full_ordering(1, 2, 4, 5)

    def test_delete_last(self):
        self.delete_ctfg(self.ctfg5)
        self.assert_full_ordering(1, 2, 3, 4)
