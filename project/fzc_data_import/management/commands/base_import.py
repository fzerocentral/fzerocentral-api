from django.core.management.base import BaseCommand
import yaml

from chart_tags.models import ChartTag
from chart_types.models import ChartType
from filters.models import Filter
from filter_groups.models import FilterGroup
from games.models import Game


class Command(BaseCommand):

    def handle(self, *args, **options):

        Game(name="F-Zero: Maximum Velocity").save()
        Game(name="F-Zero GX").save()

        # Load base filter group and filter data
        with open('fzc_data_import/data/base_filters.yaml', 'r') as yaml_file:
            filters_data = yaml.full_load(yaml_file)

        # Create base filter groups and filters
        for game_name, game_filters_data in filters_data.items():
            game = Game.objects.get(name=game_name)

            for order, fg_data in enumerate(game_filters_data, 1):
                fg = FilterGroup(
                    game=game,
                    name=fg_data['name'],
                    show_by_default=fg_data['show_by_default'],
                    description=fg_data['description'],
                    kind=getattr(FilterGroup.Kinds, fg_data['kind']).value,
                    order_in_game=order,
                )
                fg.save()

                for filter_data in fg_data['filters']:
                    if fg.kind == FilterGroup.Kinds.NUMERIC:
                        f = Filter(
                            name=filter_data[0],
                            numeric_value=filter_data[1],
                            filter_group=fg,
                        )
                    else:
                        f = Filter(
                            name=filter_data,
                            filter_group=fg,
                        )

                    f.save()
                    fg.filter_set.add(f)

        # Load chart type data
        with open('fzc_data_import/data/chart_types.yaml', 'r') as yaml_file:
            chart_types_data = yaml.full_load(yaml_file)

        # Create chart types
        for game_name, game_cts_data in chart_types_data.items():
            game = Game.objects.get(name=game_name)

            for ct_data in game_cts_data:
                filter_groups = FilterGroup.objects.filter(
                    game=game, name__in=ct_data['filter_groups'])
                ct = ChartType(
                    game=game,
                    name=ct_data['name'],
                    format_spec=ct_data['format_spec'],
                    order_ascending=ct_data['order_ascending'],
                )
                ct.save()
                ct.filter_groups.set(filter_groups)
                ct.save()

        # Load chart tag data
        with open('fzc_data_import/data/chart_tags.yaml', 'r') as yaml_file:
            chart_tags_data = yaml.full_load(yaml_file)

        # Create chart tags
        for game_name, game_tags_data in chart_tags_data.items():
            game = Game.objects.get(name=game_name)

            for tag_data in game_tags_data:
                tag_name = tag_data['name']
                primary_chart_type = ChartType.objects.get(
                    game=game, name=tag_data['primary_chart_type'])
                tag = ChartTag(
                    name=tag_name,
                    total_name=tag_data.get('total_name'),
                    game=game,
                    primary_chart_type=primary_chart_type,
                )
                tag.save()
