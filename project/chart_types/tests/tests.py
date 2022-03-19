from rest_framework import status
from rest_framework.test import APITestCase

from filter_groups.models import FilterGroup
from games.models import Game
from ..models import ChartType
from .utils import link_ct_and_fg


class ChartTypePatchTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.game = Game(name="G")
        cls.game.save()
        cls.ct1 = ChartType(
            game=cls.game, name="CT1", format_spec=[], order_ascending=True)
        cls.ct1.save()
        cls.fg1 = FilterGroup(
            game=cls.game, name="FG1", description="Test", order_in_game=1)
        cls.fg1.save()

    def test_link_fg(self):
        response = link_ct_and_fg(self.ct1, self.fg1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.ct1.refresh_from_db()
        self.assertListEqual(
            list(self.ct1.filter_groups.all().values_list('id', flat=True)),
            [self.fg1.id])
