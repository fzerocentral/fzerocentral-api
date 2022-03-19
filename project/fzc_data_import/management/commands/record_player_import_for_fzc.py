import getpass
import re
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.db.models import Count
import MySQLdb
from tqdm import tqdm
import yaml

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

    def handle(self, *args, **options):

        # Connect to the MySQL DB
        password = getpass.getpass(
            f"Enter password for MySQL user {options['mysql_user']}: ")
        mysql_conn = MySQLdb.connect(
            host=options['mysql_host'], port=options['mysql_port'],
            user=options['mysql_user'], passwd=password,
            db=options['mysql_dbname'], charset='utf8')
        mysql_cur = mysql_conn.cursor(MySQLdb.cursors.DictCursor)

        # Make a lookup of FZC PHP ladder / cup / course / record type
        # -> FZC Django chart.
        # Also a lookup of FZC PHP ladder -> filters.

        fzcphp_to_fzcdjango_chart_lookup = dict()
        fzcphp_ladders_to_filters = dict()

        with open(
                'fzc_data_import/data/fzcphp_ladder_details.yaml',
                'r') as yaml_file:
            fzcphp_ladder_details = yaml.full_load(yaml_file)

        for ladder_spec in fzcphp_ladder_details:

            php_ladder_id = ladder_spec['ladder_id']
            game = Game.objects.get(name=ladder_spec['game_name'])
            cups_cg = game.chartgroup_set.get(parent_group=None, name="Cups")

            for cup_id, cup_spec in enumerate(ladder_spec['cups'], 1):
                cup_cg = cups_cg.child_groups.get(name=cup_spec['name'])

                for course_id, course_name in enumerate(
                        cup_spec['courses'], 1):
                    course_cg = cup_cg.child_groups.get(name=course_name)

                    for record_type_code, record_type_name in ladder_spec[
                            'record_types'].items():

                        chart = course_cg.charts.get(name=record_type_name)
                        lookup_key = (
                            php_ladder_id, cup_id, course_id, record_type_code)
                        fzcphp_to_fzcdjango_chart_lookup[lookup_key] = chart

            filter_dict = ladder_spec.get('filters', dict())
            fzcphp_ladders_to_filters[php_ladder_id] = filter_dict

        # Make a lookup of known ship misspellings in the FZC PHP database.
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
            for filter in filter_group.filter_set.all():
                normalized = self.normalize_machine_name(filter.name)
                self.normalized_to_canonical_machines[normalized] = filter.name

        # Make a lookup of user id on FZC PHP -> username.
        mysql_cur.execute("SELECT user_id, username FROM phpbb_users;")
        fzcphp_user_lookup = dict(
            (u['user_id'], u['username']) for u in mysql_cur.fetchall())

        # Get FZC PHP records.
        #
        # We'll process records in a particular FZC-PHP ladder order.
        # The reason is to process ladders with more specific categories
        # first, and then more general ones after.
        # For example, if a time is found in both max speed and open ladders
        # for GX, we want to make sure we add it with max speed filters.

        # TODO: We're only processing records for GX time attack for now, but
        # should cover other ladders and games later.
        ladder_order = [
            # F-Zero GX time attack: max speed, snaking, open
            5, 8, 4,
        ]

        php_records = []
        for ladder_id in ladder_order:
            mysql_cur.execute(
                "SELECT * FROM phpbb_f0_records"
                " WHERE ladder_id = %(ladder_id)s",
                dict(ladder_id=ladder_id))
            php_records.extend(mysql_cur.fetchall())

        # Convert FZC PHP records to FZC Django records. Also link applicable
        # filters to the records.

        fzcphp_deleted_user_ids = set()
        unrecognized_ships = set()

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
            chart = fzcphp_to_fzcdjango_chart_lookup[lookup_key]
            chart_type = chart.chart_type

            # Users/Players.

            # Detect deleted users whose records still remain in FZC PHP.
            # We won't add these records, but we'll track the deleted user ids
            # to print after we're done.
            if php_record['user_id'] not in fzcphp_user_lookup:
                fzcphp_deleted_user_ids.add(php_record['user_id'])
                continue

            username = fzcphp_user_lookup[php_record['user_id']]

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
            ladder_filters = fzcphp_ladders_to_filters[
                php_record['ladder_id']]
            record_filters = []
            for filter_group_name, filter_name in ladder_filters.items():
                try:
                    filter_group = chart_type.filter_groups.get(
                        name=filter_group_name)
                except FilterGroup.DoesNotExist:
                    # This filter group presumably does not apply to this
                    # chart type. For example, checkpoint skipping does not
                    # apply to top speeds.
                    pass
                else:
                    filter = filter_group.filter_set.get(name=filter_name)
                    record_filters.append(filter)

            # Machine filter.
            machine_filter_group = chart_type.filter_groups.get(name="Machine")
            canonical_machine_name = self.get_canonical_machine_name(
                php_record['ship'])
            if canonical_machine_name:
                machine_filter = machine_filter_group.filter_set.get(
                    name=canonical_machine_name)
                record_filters.append(machine_filter)
            else:
                unrecognized_ships.add(php_record['ship'])

            record.filters.add(*record_filters)

        self.stdout.write(
            f"""
            Final counts:
            {Player.objects.all().count()} players
            {Record.objects.all().count()} records
            {Record.objects.all().aggregate(Count('filters')).get(
                'filters__count')} filter applications to records
            """)

        s = ", ".join(
            [str(user_id) for user_id in fzcphp_deleted_user_ids]) or "None"
        self.stdout.write(f"Deleted user ids found in FZC PHP: {s}")

        s = ", ".join(unrecognized_ships) or "None"
        self.stdout.write(f"Unrecognized ships: {s}")
