from django.core.management.base import BaseCommand
import yaml

from charts.models import Chart
from chart_groups.models import ChartGroup
from chart_tags.models import ChartTag
from chart_types.models import ChartType
from games.models import Game


class Command(BaseCommand):
    help = """
    Import charts from ../../data/charts.yaml into the database.
    - The relevant games and chart types are assumed to already exist.
    - Will create any charts and chart groups that don't exist yet.
    
    In charts.yaml, note that a chart can be specified as
    a hash of `name` and `type` (chart type), or as just a `name` string for
    brevity. If it's just a name string, then
    `common_elements` -> `chart_type` must be specified by the
    parent group or an ancestor group.
    
    Chart tags are derived from either of:
    - `common_elements` -> `chart_tag`
    - Chart name
    
    Example usage:
    python manage.py chart_import
    """

    def visit_chart_group(
            self, group_spec, game, parent_group, order,
            parent_common_elements):

        common_elements = parent_common_elements.copy()
        if 'common_elements' in group_spec:
            common_elements.update(group_spec['common_elements'])

        try:
            chart_group = ChartGroup.objects.get(
                game=game, parent_group=parent_group, name=group_spec['name'])
        except ChartGroup.DoesNotExist:
            chart_group = ChartGroup(
                game=game, parent_group=parent_group, name=group_spec['name'],
                order_in_parent=order,
                show_charts_together=group_spec.get(
                    'show_charts_together', False))
            chart_group.save()

        if 'child_groups' in group_spec:
            for child_order, child_group in enumerate(
                    group_spec['child_groups'], 1):
                self.visit_chart_group(
                    child_group, game, chart_group, child_order,
                    common_elements)

        if 'charts' in group_spec:
            for chart_order, chart_spec in enumerate(group_spec['charts'], 1):
                # `chart_spec` can be either a dict, or just a name string.
                if isinstance(chart_spec, str):
                    chart_name = chart_spec
                    chart_type_name = None
                    chart_specific_tag_names = None
                else:
                    chart_name = chart_spec['name']
                    chart_type_name = chart_spec.get('type')
                    chart_specific_tag_names = chart_spec.get('tags')

                if not chart_type_name:
                    if 'chart_type' not in common_elements:
                        raise ValueError(
                            f"No chart type specified for chart {chart_name}"
                            f" of group {group_spec['name']}"
                            f" (group id {chart_group.id})")
                    chart_type_name = common_elements['chart_type']

                try:
                    Chart.objects.get(
                        chart_group=chart_group, name=chart_name)
                    # Chart already exists.
                    continue
                except Chart.DoesNotExist:
                    pass

                # Create chart.

                chart_type = ChartType.objects.get(
                    game=game, name=chart_type_name)

                potential_chart_tag_names = [chart_name]
                if 'chart_tag' in common_elements:
                    # This only supports one group-wide tag. If a need
                    # arises later for multiple group-wide tags, then this
                    # would have to be changed.
                    potential_chart_tag_names.append(
                        common_elements['chart_tag'])
                if chart_specific_tag_names:
                    potential_chart_tag_names.extend(
                        chart_specific_tag_names)

                tags = ChartTag.objects.filter(
                    game=game, name__in=potential_chart_tag_names)

                chart = Chart(
                    chart_group=chart_group, name=chart_name,
                    order_in_group=chart_order, chart_type=chart_type,
                )
                chart.save()
                chart.chart_tags.set(tags)
                chart.save()

    def handle(self, *args, **options):

        # Load chart data
        with open('fzc_data_import/data/charts.yaml', 'r') as yaml_file:
            charts_data = yaml.full_load(yaml_file)

        # Add chart groups and charts as necessary
        for game_name, game_top_level_groups in charts_data.items():
            game = Game.objects.get(name=game_name)
            for order, group_spec in enumerate(game_top_level_groups, 1):
                self.visit_chart_group(group_spec, game, None, order, dict())

        # Check object counts

        self.stdout.write("Final counts:")

        for game_name in charts_data.keys():
            game = Game.objects.get(name=game_name)
            group_count = ChartGroup.objects.filter(game=game).count()
            chart_count = Chart.objects.filter(chart_group__game=game).count()
            self.stdout.write(
                f"{game_name}: {group_count} groups, {chart_count} charts")
