import datetime
import getpass
import re
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.db.models import Count
import MySQLdb
from tqdm import tqdm
import yaml

from chart_groups.models import ChartGroup
from charts.models import Chart
from filter_groups.models import FilterGroup
from games.models import Game
from players.models import Player
from records.models import Record


class Command(BaseCommand):
    help = """
    Import records and players from the old FZC database.
    
    Example usage:
    python manage.py record_player_import_for_fzc localhost 3306 fzc_php root
    """

    @staticmethod
    def normalize_machine_name(name):
        # Remove spaces and some punctuation.
        name = re.sub(r'[\s\-/_]+', '', name)
        # Uppercase to lowercase.
        return name.lower()

    def get_canonical_machine_name(self, name):
        normalized_name = self.normalize_machine_name(name)

        if normalized_name in self.ship_misspellings:
            # Known misspelling in the FZC PHP database.
            return self.ship_misspellings[normalized_name]
        elif normalized_name in self.normalized_to_canonical_machines:
            return self.normalized_to_canonical_machines[normalized_name]
        else:
            # Unrecognized name
            return None

    def add_arguments(self, parser):
        parser.add_argument(
            'mysql_host',
            type=str,
            help="Host of the MySQL server"
                 " (can be 'localhost' if local machine)")
        parser.add_argument(
            'mysql_port',
            type=int,
            help="Port of the MySQL server (MySQL default is 3306)")
        parser.add_argument(
            'mysql_dbname',
            type=str,
            help="Name of the MySQL database")
        parser.add_argument(
            'mysql_user',
            type=str,
            help="MySQL user to authenticate as")

    def visit_chart_group(self, cg, cg_spec, php_ladder_id, game, ladder_spec):

        for name, content in cg_spec.items():
            if isinstance(content, str):
                cup_id, course_id = content.split('-')
                cup_id = int(cup_id)
                course_id = int(course_id)

                if 'record_type' in ladder_spec:
                    # Only one recognized record type, so the name will be
                    # a chart name in FZC Django, not a chart group name.
                    rt_code = ladder_spec['record_type']
                    chart_name = name
                    chart = Chart.objects.get(
                        chart_group=cg, name=chart_name)
                    key = (
                        php_ladder_id, cup_id, course_id, rt_code)
                    self.php_to_django_chart_lookup[key] = chart
                else:
                    # Multiple record types.
                    record_types = ladder_spec['record_types']
                    cg_name = name
                    child_cg = ChartGroup.objects.get(
                        game=game, parent_group=cg, name=cg_name)
                    for rt_code, rt_name in record_types.items():
                        chart = child_cg.charts.get(name=rt_name)
                        key = (
                            php_ladder_id, cup_id, course_id, rt_code)
                        self.php_to_django_chart_lookup[key] = chart

                if 'ignored_record_types' in ladder_spec:
                    for rt_code in ladder_spec['ignored_record_types']:
                        key = (php_ladder_id, cup_id, course_id, rt_code)
                        self.php_ignored_charts.add(key)
            else:
                cg_name = name
                child_cg = ChartGroup.objects.get(
                    game=game, parent_group=cg, name=cg_name)
                self.visit_chart_group(
                    child_cg, content, php_ladder_id, game, ladder_spec)

    def process_records(self, game_name, php_ladder_ids):
        """Process records for a particular game."""

        game = Game.objects.get(name=game_name)

        # Make a lookup of filter IDs.
        filter_lookup = dict()
        for filter_group in game.filtergroup_set.all():
            filter_lookup[filter_group.name] = dict()
            for filter_vs in filter_group.filter_set.values('id', 'name'):
                filter_lookup[filter_group.name][filter_vs['name']] = \
                    filter_vs['id']

        # Make a lookup of filter groups of each chart type.
        ctfg_lookup = dict()
        for chart_type in game.charttype_set.all():
            fg_names = chart_type.filter_groups.values_list('name', flat=True)
            ctfg_lookup[chart_type.id] = set(fg_names)

        # Get FZC PHP records.

        php_records = []
        for php_ladder_id in php_ladder_ids:
            self.mysql_cur.execute(
                "SELECT * FROM phpbb_f0_records"
                " WHERE ladder_id = %(ladder_id)s",
                dict(ladder_id=php_ladder_id))
            php_records.extend(self.mysql_cur.fetchall())

        # Convert FZC PHP records to FZC Django records. Also link applicable
        # filters to the records.

        fzcphp_deleted_user_ids = set()
        unrecognized_ships = set()

        self.stdout.write(
            f"""
            -----
            {game_name}: processing records
            -----
            """)

        for php_record in tqdm(php_records):
            # value column is already the same.
            value = php_record['value']

            # last_change is the only date field on FZC PHP records, so we use
            # that, even if it's not the same as achievement date.
            # TODO: Double check if this timezone is correct for FZC's
            # existing data.
            date_achieved = php_record['last_change'].replace(
                tzinfo=ZoneInfo("UTC"))

            # Several FZC PHP columns correspond to chart.
            lookup_key = (
                php_record['ladder_id'],
                php_record['cup_id'],
                php_record['course_id'],
                php_record['record_type'])
            if lookup_key in self.php_ignored_charts:
                continue
            chart = self.php_to_django_chart_lookup[lookup_key]
            chart_type_fg_names = ctfg_lookup[chart.chart_type_id]

            # Users/Players.

            # Detect deleted users whose records still remain in FZC PHP.
            # We won't add these records, but we'll track the deleted user ids
            # to print after we're done.
            if php_record['user_id'] not in self.fzcphp_user_lookup:
                fzcphp_deleted_user_ids.add(php_record['user_id'])
                continue

            username = self.fzcphp_user_lookup[php_record['user_id']]

            # Create a new player in FZC Django if needed.
            try:
                player = Player.objects.get(username=username)
            except Player.DoesNotExist:
                player = Player(username=username)
                player.save()

            # See if the record exists.
            # We'll assume that same chart + same player + same time/score
            # means the same record.
            try:
                Record.objects.get(chart=chart, player=player, value=value)
            except Record.DoesNotExist:
                pass
            else:
                # The record exists, so we're done here.
                continue

            # Create the record.
            record = Record(
                value=value,
                date_achieved=date_achieved,
                chart=chart,
                player=player,
            )
            record.save()

            # Set the record's filters.

            # Filters specified in YAML.
            ladder_filters = self.fzcphp_ladders_to_filters[
                php_record['ladder_id']]
            record_filters = []
            for filter_group_name, filter_name in ladder_filters.items():
                if filter_group_name not in chart_type_fg_names:
                    # This filter group does not apply to this chart type.
                    # For example, checkpoint skipping does not apply to
                    # top speeds.
                    pass
                else:
                    filter_id = filter_lookup[filter_group_name][filter_name]
                    record_filters.append(filter_id)

            # Machine filter.
            if "Machine" not in chart_type_fg_names:
                # No machine selection for this chart type.
                pass
            elif game_name == "F-Zero GX":
                canonical_machine_name = self.get_canonical_machine_name(
                    php_record['ship'])
                if canonical_machine_name:
                    # We recognize this machine name or know how to fix it.
                    filter_id = \
                        filter_lookup["Machine"][canonical_machine_name]
                    record_filters.append(filter_id)
                elif php_record['ship'] == '':
                    # No machine specified.
                    pass
                else:
                    # Don't know how to fix this machine name.
                    unrecognized_ships.add(php_record['ship'])
            else:
                # Machines for games other than GX are straightforward.
                filter_id = filter_lookup["Machine"][php_record['ship']]
                record_filters.append(filter_id)

            record.filters.add(*record_filters)

        self.stdout.write(
            f"""
            Counts:
            {game.record_set.count()} records
            {game.record_set.aggregate(Count('filters')).get(
                'filters__count')} filter applications to records
            """
        )

        s = ", ".join(
            [str(user_id) for user_id in fzcphp_deleted_user_ids]) or "None"
        self.stdout.write(f"Deleted user ids with records in FZC PHP: {s}")

        s = ", ".join(unrecognized_ships) or "None"
        self.stdout.write(f"Unrecognized ships: {s}")

    def handle(self, *args, **options):

        # Connect to the MySQL DB
        password = getpass.getpass(
            f"Enter password for MySQL user {options['mysql_user']}: ")
        mysql_conn = MySQLdb.connect(
            host=options['mysql_host'], port=options['mysql_port'],
            user=options['mysql_user'], passwd=password,
            db=options['mysql_dbname'], charset='utf8')
        self.mysql_cur = mysql_conn.cursor(MySQLdb.cursors.DictCursor)

        start_time = datetime.datetime.now()

        # Make a lookup of FZC PHP ladder / cup / course / record type
        # -> FZC Django chart.
        # Also a lookup of FZC PHP ladder -> filters.

        self.php_to_django_chart_lookup = dict()
        self.php_ignored_charts = set()
        self.fzcphp_ladders_to_filters = dict()

        with open(
                'fzc_data_import/data/fzcphp_ladder_details.yaml',
                'r') as yaml_file:
            fzcphp_ladder_details = yaml.full_load(yaml_file)

        for ladder_spec in fzcphp_ladder_details:

            php_ladder_id = ladder_spec['ladder_id']
            game = Game.objects.get(name=ladder_spec['game_name'])
            charts_spec = ladder_spec['charts']

            self.visit_chart_group(
                None, charts_spec, php_ladder_id, game, ladder_spec)

            filter_dict = ladder_spec.get('filters', dict())
            self.fzcphp_ladders_to_filters[php_ladder_id] = filter_dict

        # Make a lookup of known GX ship misspellings in the FZC PHP database.
        with open(
                'fzc_data_import/data/ship_misspellings.yaml',
                'r', encoding='utf-8') as yaml_file:
            misspellings_data = yaml.full_load(yaml_file)

        self.ship_misspellings = dict()
        for misspelling, canonical_name in misspellings_data.items():
            self.ship_misspellings[
                self.normalize_machine_name(misspelling)] = canonical_name

        # Make a lookup of normalized machine names to canonical machine names.
        self.normalized_to_canonical_machines = dict()
        for filter_group in FilterGroup.objects.filter(name="Machine"):
            for f in filter_group.filter_set.all():
                normalized = self.normalize_machine_name(f.name)
                self.normalized_to_canonical_machines[normalized] = f.name

        # Make a lookup of user id on FZC PHP -> username.
        self.mysql_cur.execute("SELECT user_id, username FROM phpbb_users;")
        self.fzcphp_user_lookup = dict(
            (u['user_id'], u['username']) for u in self.mysql_cur.fetchall())

        # Process PHP records and add them as Django records.
        # We'll process records by game. We'll also process in a particular
        # FZC-PHP ladder order: more specific categories first, and then more
        # general ones after.
        # For example, if a time is found in both max speed and open ladders
        # for GX, we want to make sure we add it with max speed filters.
        all_php_ladder_ids = {
            "F-Zero GX": [
                # F-Zero GX story: max speed, snaking
                11, 12,
                # F-Zero GX time attack: max speed, snaking, open
                5, 8, 4,
            ],
        }

        for game_name, php_ladder_ids in all_php_ladder_ids.items():
            self.process_records(game_name, php_ladder_ids)

        end_time = datetime.datetime.now()

        self.stdout.write(
            f"""
            -----
            Overall counts
            -----
            {Player.objects.all().count()} players
            {Record.objects.all().count()} records
            {Record.objects.all().aggregate(Count('filters')).get(
                'filters__count')} filter applications to records
            Time taken to import: {end_time - start_time}
            """
        )
