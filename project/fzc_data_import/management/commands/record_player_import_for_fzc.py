import datetime
import getpass
import re
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.db.models import Count
import MySQLdb
import yaml

from chart_groups.models import ChartGroup
from charts.models import Chart
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
        name = re.sub(r'[\s\-./_]+', '', name)
        # Uppercase to lowercase.
        return name.lower()

    def get_canonical_machine_name(
            self, canonical_lookup, misspell_lookup, name):
        normalized_name = self.normalize_machine_name(name)

        if normalized_name in misspell_lookup:
            # Known misspelling in the FZC PHP database.
            return misspell_lookup[normalized_name]
        elif normalized_name in canonical_lookup:
            return canonical_lookup[normalized_name]
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
        parser.add_argument(
            '--clear_existing',
            action='store_true',
            help="Clear all existing records and players in the Django DB")

    def visit_chart_group(self, cg, cg_spec, php_ladder_id, game, ladder_spec):

        for name, content in cg_spec.items():
            if isinstance(content, str):
                cup_id, course_id = content.split('-')
                cup_id = int(cup_id)
                course_id = int(course_id)

                for rt in ladder_spec['record_types']:
                    key = (php_ladder_id, cup_id, course_id, rt['old'])

                    if rt['new'] is None:
                        # Ignore this record type.
                        chart = None
                    elif rt['new'] is True:
                        # Only one recognized record type, so the name will be
                        # a chart name in FZC Django, not a chart group name.
                        chart_name = name
                        chart = Chart.objects.get(
                            chart_group=cg, name=chart_name)
                    else:
                        # Multiple record types to import, so the name will be
                        # a chart group name, and the record type will specify
                        # the chart name.
                        cg_name = name
                        child_cg = ChartGroup.objects.get(
                            game=game, parent_group=cg, name=cg_name)
                        chart = child_cg.charts.get(name=rt['new'])

                    lookup_result = dict(chart=chart)
                    if 'value_divisor' in rt:
                        lookup_result['value_divisor'] = rt['value_divisor']
                    self.php_to_django_chart_lookup[key] = lookup_result
            else:
                cg_name = name
                child_cg = ChartGroup.objects.get(
                    game=game, parent_group=cg, name=cg_name)
                self.visit_chart_group(
                    child_cg, content, php_ladder_id, game, ladder_spec)

    def process_records(self, game_name, php_ladder_ids):
        """Process records for a particular game."""

        game = Game.objects.get(name=game_name)

        # Make a lookup of known ship misspellings in the FZC PHP database.
        game_misspell_data = self.misspellings_data[game_name]
        misspell_lookup = dict()
        for misspelling, canonical_name in game_misspell_data.items():
            normalized = self.normalize_machine_name(misspelling)
            misspell_lookup[normalized] = canonical_name

        # Make a lookup of normalized machine names to canonical machine names.
        canonical_lookup = dict()
        machine_fg = game.filtergroup_set.get(name="Machine")
        for f in machine_fg.filter_set.all():
            normalized = self.normalize_machine_name(f.name)
            canonical_lookup[normalized] = f.name

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

        record_lookup = dict()
        RecordFilterModel = Record.filters.through

        for php_record in php_records:
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
            chart_lookup_entry = self.php_to_django_chart_lookup[lookup_key]
            chart = chart_lookup_entry['chart']
            if chart is None:
                continue
            chart_type_fg_names = ctfg_lookup[chart.chart_type_id]

            # value might need a divisor. For example, to convert milliseconds
            # to centiseconds.
            value = php_record['value']
            if 'value_divisor' in chart_lookup_entry:
                value /= chart_lookup_entry['value_divisor']

            # Users/Players.

            # Detect deleted users whose records still remain in FZC PHP.
            # We won't add these records, but we'll track the deleted user ids
            # to print after we're done.
            if php_record['user_id'] not in self.fzcphp_user_lookup:
                fzcphp_deleted_user_ids.add(php_record['user_id'])
                continue

            username = self.fzcphp_user_lookup[php_record['user_id']]

            # Create a new player in FZC Django if needed.
            if username in self.player_lookup:
                player_id = self.player_lookup[username]
            else:
                player = Player(username=username)
                player.save()
                player_id = player.id
                self.player_lookup[username] = player_id

            # See if the record exists.
            # We'll assume that same chart + same player + same time/score
            # means the same record.
            record_key = (chart.id, player_id, value)
            if record_key in record_lookup:
                # The record exists, so we're done here.
                continue

            # Prepare the record.
            record = Record(
                value=value,
                date_achieved=date_achieved,
                chart=chart,
                player_id=player_id,
            )

            # Prepare the record's filters.

            # Filters specified in YAML.
            ladder_filters = self.fzcphp_ladders_to_filters[
                php_record['ladder_id']]
            filter_ids = []
            for filter_group_name, filter_name in ladder_filters.items():
                if filter_group_name not in chart_type_fg_names:
                    # This filter group does not apply to this chart type.
                    # For example, checkpoint skipping does not apply to
                    # top speeds.
                    pass
                else:
                    filter_id = filter_lookup[filter_group_name][filter_name]
                    filter_ids.append(filter_id)

            # Machine filter.
            if "Machine" not in chart_type_fg_names:
                # No machine selection for this chart type.
                pass
            else:
                canonical_machine_name = self.get_canonical_machine_name(
                    canonical_lookup, misspell_lookup, php_record['ship'])
                if canonical_machine_name:
                    # We recognize this machine name or know how to fix it.
                    filter_id = \
                        filter_lookup["Machine"][canonical_machine_name]
                    filter_ids.append(filter_id)
                elif php_record['ship'].strip() == '':
                    # No machine specified.
                    pass
                else:
                    # Don't know how to fix this machine name.
                    unrecognized_ships.add(php_record['ship'])

            record_lookup[record_key] = dict(
                record=record, filter_ids=filter_ids)

        self.stdout.write("Bulk-creating records")

        # Create the records.
        record_list = [
            entry['record'] for entry in record_lookup.values()]
        created_record_list = Record.objects.bulk_create(record_list)

        # Create the record-filter associations.
        filter_ids_list = [
            entry['filter_ids'] for entry in record_lookup.values()]
        record_filter_list = []
        for index, record in enumerate(created_record_list):
            filter_ids = filter_ids_list[index]
            record_filters = [
                RecordFilterModel(record_id=record.id, filter_id=filter_id)
                for filter_id in filter_ids
            ]
            record_filter_list.extend(record_filters)
        RecordFilterModel.objects.bulk_create(record_filter_list)

        # Print stats.

        game_records = Record.objects.filter(
            chart__chart_group__game=game)
        self.stdout.write(
            f"""
            Counts:
            {game_records.count()} records
            {game_records.aggregate(Count('filters')).get(
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

        if options['clear_existing']:
            self.stdout.write("Clearing existing records/players...")
            Record.objects.all().delete()
            Player.objects.all().delete()
            self.stdout.write("Done")

        start_time = datetime.datetime.now()

        # Make a lookup of FZC PHP ladder / cup / course / record type
        # -> FZC Django chart.
        # Also a lookup of FZC PHP ladder -> filters.

        self.php_to_django_chart_lookup = dict()
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

        # Load known ship misspellings.
        with open(
                'fzc_data_import/data/ship_misspellings.yaml',
                'r', encoding='utf-8') as yaml_file:
            self.misspellings_data = yaml.full_load(yaml_file)

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
            "F-Zero: Maximum Velocity": [3],
            "F-Zero GX": [
                # F-Zero GX story: max speed, snaking
                11, 12,
                # F-Zero GX time attack: max speed, snaking, open
                5, 8, 4,
            ],
        }

        existing_players = Player.objects.all()
        self.player_lookup = {
            p['username']: p['id']
            for p in existing_players.values('id', 'username')
        }

        for game_name, php_ladder_ids in all_php_ladder_ids.items():
            self.process_records(game_name, php_ladder_ids)

        end_time = datetime.datetime.now()

        # Print stats.

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
