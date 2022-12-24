from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = """
    Populate the FZC database from scratch. Assumes the migration structure is
    there, but no data.
    
    Example usage:
    python manage.py full_ranking_import_fzc localhost 3306 fzc_php root
    
    Note that you can clear the data (without clearing the table structure)
    with `python manage.py flush`.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            'mysql_host', help="See record_player_import_fzc command")
        parser.add_argument(
            'mysql_port',
            type=int, help="See record_player_import_fzc command")
        parser.add_argument(
            'mysql_dbname', help="See record_player_import_fzc command")
        parser.add_argument(
            'mysql_user', help="See record_player_import_fzc command")

    def handle(self, *args, **options):

        call_command('base_import_fzc')
        call_command('chart_import')
        call_command(
            'filter_import', 'fzc_data_import/data/gx_machine_filters.csv')
        call_command('ladder_import')
        call_command(
            'record_player_import_fzc',
            *[options[arg_name] for arg_name in
              ['mysql_host', 'mysql_port', 'mysql_dbname', 'mysql_user']])
