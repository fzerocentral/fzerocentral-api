from django.core.management.base import BaseCommand
import yaml

from chart_groups.models import ChartGroup
from chart_tags.models import ChartTag
from filters.models import Filter
from games.models import Game
from ladders.models import Ladder, LadderChartTag


class Command(BaseCommand):

    def handle(self, *args, **options):

        # Load ladder data
        with open('fzc_data_import/data/ladders.yaml', 'r') as yaml_file:
            ladders_data = yaml.full_load(yaml_file)

        # Add ladders
        for game_name, game_ladders_data in ladders_data.items():
            game = Game.objects.get(name=game_name)
            main_order = 0
            side_order = 0

            for ladder_data in game_ladders_data:
                kind = getattr(Ladder.Kinds, ladder_data['kind']).value
                if kind == Ladder.Kinds.MAIN.value:
                    main_order += 1
                    order = main_order
                else:
                    side_order += 1
                    order = side_order

                chart_group = ChartGroup.objects.get(
                    name=ladder_data['chart_group'])

                filter_spec_parts = []
                for filter_data in ladder_data.get('filters', []):
                    f = Filter.objects.get(
                        filter_group__name=filter_data['group'],
                        name=filter_data['name'],
                    )

                    modifier = ''
                    if 'modifier' in filter_data:
                        modifier = getattr(
                            Filter.SpecModifiers,
                            filter_data['modifier']).value

                    filter_spec_parts.append(f'{f.id}{modifier}')

                ladder = Ladder(
                    game=game,
                    name=ladder_data['name'],
                    kind=kind,
                    order_in_game_and_kind=order,
                    chart_group=chart_group,
                    filter_spec='-'.join(filter_spec_parts),
                )
                ladder.save()

                tags_data = ladder_data.get('chart_tags', dict())
                for tag_name, tag_weight in tags_data.items():
                    chart_tag = ChartTag.objects.get(game=game, name=tag_name)
                    ladder_tag = LadderChartTag(
                        ladder=ladder,
                        chart_tag=chart_tag,
                        weight=tag_weight,
                    )
                    ladder_tag.save()
