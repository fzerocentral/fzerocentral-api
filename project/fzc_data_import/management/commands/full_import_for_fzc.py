from django.core.management import call_command
from django.core.management.base import BaseCommand

from chart_types.models import ChartType
from filters.models import Filter
from filter_groups.models import FilterGroup
from games.models import Game


class Command(BaseCommand):
    help = """
    Populate the FZC database from scratch. Assumes the migration structure is
    there, but no data.
    
    Example usage:
    python manage.py full_import_for_fzc localhost 3306 fzc_php root
    
    Note that you can clear the data (without clearing the table structure)
    with `python manage.py flush`.
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
            game=g, name="Machine",
            show_by_default=True, order_in_game=1,
            description="Racing machine used for the run.",
            kind=FilterGroup.Kinds.SELECT.value)
        machine.save()
        setting = FilterGroup(
            game=g, name="Setting",
            show_by_default=True, order_in_game=2,
            description="Acceleration/max speed setting used for the run."
                        " 0% all the way at the left, 100% all the way at"
                        " the right.",
            kind=FilterGroup.Kinds.NUMERIC.value)
        setting.save()
        Filter(name="0%", numeric_value=0, filter_group=setting).save()
        Filter(name="100%", numeric_value=100, filter_group=setting).save()
        checks = FilterGroup(
            game=g, name="Checkpoint skips",
            show_by_default=False, order_in_game=3,
            description="Whether checkpoint skipping"
                        " was used in the run or not.",
            kind=FilterGroup.Kinds.SELECT.value)
        checks.save()
        Filter(name="Yes", filter_group=checks).save()
        Filter(name="No", filter_group=checks).save()

        for ct in [course, lap, speed]:
            ct.filter_groups.add(machine, setting)
        for ct in [course, lap]:
            ct.filter_groups.add(checks)

        call_command('chart_import')
        call_command(
            'filter_import', 'fzc_data_import/data/gx_machine_filters.csv')
        call_command(
            'record_player_import_for_fzc',
            *[options[arg_name] for arg_name in
              ['mysql_host', 'mysql_port', 'mysql_dbname', 'mysql_user']])
