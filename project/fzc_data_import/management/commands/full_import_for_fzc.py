from django.core.management import call_command
from django.core.management.base import BaseCommand

from chart_types.models import ChartType, CTFG
from filters.models import Filter
from filter_groups.models import FilterGroup
from games.models import Game


class Command(BaseCommand):
    help = """
    Populate the FZC database from scratch.
    
    Example usage:
    python manage.py full_import_for_fzc localhost 3306 fzc_php root
    """

    def add_arguments(self, parser):
        parser.add_argument(
            'mysql_host', help="See record_player_import_for_fzc command")
        parser.add_argument(
            'mysql_port',
            type=int, help="See record_player_import_for_fzc command")
        parser.add_argument(
            'mysql_dbname', help="See record_player_import_for_fzc command")
        parser.add_argument(
            'mysql_user', help="See record_player_import_for_fzc command")

    def handle(self, *args, **options):
        g = Game(name="F-Zero GX")
        g.save()

        gx_time_spec = [
            dict(multiplier=60, suffix="'"),
            dict(multiplier=1000, suffix='"', digits=2),
            dict(digits=3)]
        course = ChartType(
            game=g, name="Course Time", format_spec=gx_time_spec,
            order_ascending=True)
        course.save()
        lap = ChartType(
            game=g, name="Lap Time", format_spec=gx_time_spec,
            order_ascending=True)
        lap.save()
        speed = ChartType(
            game=g, name="Speed", format_spec=[dict(suffix=" km/h")],
            order_ascending=False)
        speed.save()

        machine = FilterGroup(
            name="Machine", description="Racing machine used for the run.",
            kind=FilterGroup.Kinds.SELECT.value)
        machine.save()
        setting = FilterGroup(
            name="Setting",
            description="Acceleration/max speed setting used for the run."
                        " 0% all the way at the left, 100% all the way at"
                        " the right.",
            kind=FilterGroup.Kinds.NUMERIC.value)
        setting.save()
        Filter(name="0%", numeric_value=0, filter_group=setting).save()
        Filter(name="100%", numeric_value=100, filter_group=setting).save()
        checks = FilterGroup(
            name="Checkpoint skips",
            description="Whether checkpoint skipping"
                        " was used in the run or not.",
            kind=FilterGroup.Kinds.SELECT.value)
        checks.save()
        Filter(name="Yes", filter_group=checks).save()
        Filter(name="No", filter_group=checks).save()

        for ct in [course, lap, speed]:
            CTFG(
                chart_type=ct, filter_group=machine,
                show_by_default=True, order_in_chart_type=1).save()
            CTFG(
                chart_type=ct, filter_group=setting,
                show_by_default=True, order_in_chart_type=2).save()
        for ct in [course, lap]:
            CTFG(
                chart_type=ct, filter_group=checks,
                show_by_default=True, order_in_chart_type=3).save()

        call_command('chart_import')
        call_command(
            'filter_import', 'fzc_data_import/data/gx_machine_filters.csv')
        call_command(
            'record_player_import_for_fzc',
            *[options[arg_name] for arg_name in
              ['mysql_host', 'mysql_port', 'mysql_dbname', 'mysql_user']])
