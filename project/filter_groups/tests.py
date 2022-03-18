from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from charts.models import Chart
from chart_groups.models import ChartGroup
from chart_types.models import ChartType
from chart_types.tests.utils import create_ctfg
from filter_groups.models import FilterGroup
from games.models import Game


class FilterGroupIndexTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.game = Game(name="G")
        cls.game.save()
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

        cls.fg1 = FilterGroup(name="FG1")
        cls.fg1.save()
        cls.fg2 = FilterGroup(name="FG2")
        cls.fg2.save()
        cls.fg3 = FilterGroup(name="FG3")
        cls.fg3.save()
        cls.fg4 = FilterGroup(name="FG4")
        cls.fg4.save()

        # Add FGs to CT1 in different order from alphabetical, CT ID,
        # or CTFG ID, so we can tell the order field is respected.
        create_ctfg(cls.ct1, cls.fg1)
        create_ctfg(cls.ct1, cls.fg3)
        create_ctfg(cls.ct1, cls.fg2, order=1)

        # Add FGs to CT2, with at least one not in CT1, so that we can tell
        # we're only getting FGs of CT1.
        create_ctfg(cls.ct2, cls.fg3)
        create_ctfg(cls.ct2, cls.fg4)

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
