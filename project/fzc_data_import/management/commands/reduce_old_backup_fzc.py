from io import StringIO
import os
from pathlib import Path
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand
import MySQLdb

from ...utils import readable_text_stream


POSSIBLE_INPUT_DATABASE_NAMES = [
    'fzero',
    'fileand6_mfoforums',
]

POSSIBLE_VIEW_DEFINER_NAMES = [
    'fileand6_mfoadmi',
    'fileand6',
]

POSSIBLE_VIEW_NAMES = [
    'fzero_courses',
    'fzero_cups',
    'fzero_players',
    'fzero_records',
    'fzero_totals',
]

# This has:
# - All post IDs in the F-Zero Stuff forum, as of the final forum backup;
#   this includes the WR-list posts (including older versions) and the
#   rules posts, which are both useful to have historical records of.
# - The GPL and Climax WR-list post IDs, the only two such posts which
#   weren't in the F-Zero Stuff forum.
POST_IDS_TO_SAVE = [524, 525, 527, 528, 536, 537, 538, 540, 541, 542, 570, 572, 573, 574, 578, 579, 595, 598, 602, 605, 624, 812, 816, 1219, 1221, 1561, 1562, 1563, 1564, 1565, 1821, 1919, 1944, 2133, 2134, 2135, 2136, 2137, 2138, 2139, 2140, 2141, 2142, 2143, 2144, 2145, 2146, 2147, 2148, 2153, 2154, 2155, 2157, 2158, 2159, 2242, 2246, 2247, 2248, 2249, 2250, 2251, 2255, 2257, 2258, 2264, 2266, 2267, 2269, 2270, 2271, 2273, 2274, 2275, 2278, 2279, 2448, 2450, 2451, 2452, 2454, 2455, 2456, 2457, 2458, 2459, 2460, 2461, 2462, 2463, 2464, 2465, 2467, 2468, 2469, 2522, 2524, 2568, 2569, 2570, 2571, 2572, 2573, 2574, 2576, 2725, 2736, 2737, 2738, 2894, 2951, 3493, 3494, 3496, 3497, 3499, 3500, 3501, 3502, 3503, 3504, 3505, 3506, 5956, 6219, 6221, 6222, 8222, 10109, 10110, 10111, 10112, 11986, 11987, 11988, 11989, 11990, 11992, 11993, 11994, 11995, 11996, 11997, 13071, 13072, 13073, 13074, 13075, 13076, 13077, 13078, 13079, 13080, 13104, 13105, 13106, 13107, 13108, 13109, 13110, 13111, 16102, 21324, 21326, 21327, 21328, 21329, 21601, 21602, 21969, 24561, 24669, 24744, 24745, 28800, 29173, 71546, 75346, 95110, 96444, 96977, 97445, 98906, 99085, 99086, 99087, 99146, 99150, 101324, 101350, 101351, 101406, 101408, 101409, 101410, 101416, 101679, 101680, 101681, 101682, 101683, 101689, 101690, 101691, 101692, 101693, 102955, 103407, 103538]


def replace_database_name(line):
    for name in POSSIBLE_INPUT_DATABASE_NAMES:
        if name in line:
            temp_name = f'temp_{name}_reduced_version'
            return line.replace(name, temp_name), temp_name
    raise ValueError(
        f"Couldn't find an expected database name in this line: {line}")


def database_name_from_comment(line):
    for name in POSSIBLE_INPUT_DATABASE_NAMES:
        if name in line:
            return f'temp_{name}_reduced_version'
    raise ValueError(
        f"Couldn't find an expected database name in this line: {line}")


def replace_view_definer(line):
    for name in POSSIBLE_VIEW_DEFINER_NAMES:
        if f"DEFINER=`{name}`@`localhost`" in line:
            return line.replace(name, settings.OLD_FZC_DATABASE_USER)


class Command(BaseCommand):
    help = """
    Takes a gzipped backup of the old FZC database, and outputs a gzipped
    reduced backup which only has the data relevant for importing
    historical records. This is good for:
    1) Scrubbing old credentials like passwords, and PII like email addresses.
    2) Speeding up importing of historical records, since the backups are
       smaller.
    3) Reducing file storage requirements of old backups.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            'raw_backup_path',
            type=str,
            help="Full backup file from old FZC, gzipped or not.",
        )
        parser.add_argument(
            '--reduced_backup_path',
            type=str,
            help="""
            Output path for the reduced backup file. If not specified,
            this is based off of the raw backup path.
            """,
        )

    def handle(self, *args, **options):

        # Specify the password as an environment variable, and restore the
        # previous value (if any) at the end.
        old_mysql_pwd = os.environ.get('MYSQL_PWD')
        os.environ['MYSQL_PWD'] = settings.OLD_FZC_DATABASE_PASSWORD
        try:
            self.run(**options)
        finally:
            if old_mysql_pwd is None:
                del os.environ['MYSQL_PWD']
            else:
                os.environ['MYSQL_PWD'] = old_mysql_pwd

    @staticmethod
    def run(**options):

        raw_backup_path = Path(options['raw_backup_path'])
        temp_database_name = None
        with (
            readable_text_stream(raw_backup_path)
            as raw_sql_stream
        ):
            new_sql_stream = StringIO()

            for line in raw_sql_stream:

                # These are the two lines of the backup stream where we
                # need to change the database name, to define where the
                # data will be restored to.
                # We change the name from the one actually used in production,
                # to something unlikely to cause conflicts or confusion.
                if (
                    line.startswith("CREATE DATABASE")
                    or line.startswith("USE `")
                ):
                    line, temp_database_name = replace_database_name(line)

                # Other DB backups just have the database name in a comment
                # line like this.
                # This DOES indicate that the database needs to be created
                # and switched to, so we add lines to do so here.
                elif (
                    line.startswith("-- Database: `")
                    or line.startswith("-- Host: localhost    Database: ")
                ):
                    temp_database_name = database_name_from_comment(line)
                    new_sql_stream.write(
                        f"CREATE DATABASE `{temp_database_name}`;\n")
                    new_sql_stream.write(
                        f"USE `{temp_database_name}`;\n")

                # View creation; in some of the backups from 2021.04 or
                # earlier.
                elif line.startswith("CREATE ALGORITHM"):
                    # We'll get an error if the DEFINER on the view is a user
                    # that doesn't exist in this MySQL server.
                    # So we replace the DEFINER.
                    line = replace_view_definer(line)

                new_sql_stream.write(line)

        if temp_database_name is None:
            raise ValueError(
                "No database name found in the stream."
                " Perhaps double check if it was a SQL dump stream?")

        # Load into a new MariaDB database, with the previously established
        # database name. The sole purpose of this database is to allow us to
        # manipulate the data (e.g. deleting certain tables) before making a
        # new dump. We'll then delete the database to clean up.

        # https://stackoverflow.com/questions/163542/how-do-i-pass-a-string-into-subprocess-popen-using-the-stdin-argument
        subprocess.run(
            # Username = root. Password is taken care of with an environment
            # variable.
            ['mysql', '-u', 'root'],
            input=new_sql_stream.getvalue(),
            text=True,
            encoding='utf-8',
        )

        # Connect to our temporary database. Again, password is specified via
        # environment variable.
        mysql_conn = MySQLdb.connect(
            host=settings.OLD_FZC_DATABASE_HOST,
            port=settings.OLD_FZC_DATABASE_PORT,
            user=settings.OLD_FZC_DATABASE_USER,
            db=temp_database_name,
            charset='utf8',
        )
        cursor = mysql_conn.cursor()

        # Delete tables we don't need.

        cursor.execute("SHOW TABLES")
        all_tables = set([
            result[0] for result in cursor.fetchall()
        ])

        tables_to_keep = {
            # Essential data for FZC records.
            'phpbb_f0_records',
            'phpbb_users',
            # Could be useful for historical snapshots of rankings,
            # including any bugs / idiosyncracies of the ranking logic
            # at that time.
            'phpbb_f0_champs_10',
            'phpbb_f0_totals',
            # See the POST_IDS_TO_SAVE comment on the types of posts
            # we're interested in saving edit histories of.
            'phpbb_posts',
        }
        tables_to_drop = all_tables - tables_to_keep

        for table_name in tables_to_drop:
            if table_name in POSSIBLE_VIEW_NAMES:
                # It can actually be a view or a table. This is the view case.
                cursor.execute(
                    # The usual input-sanitization stuff from MySQLdb
                    # (like `%(var)s`) doesn't seem to be supported for a schema
                    # related command like this. So we just have an f-string.
                    f"DROP VIEW {table_name}",
                )
            else:
                cursor.execute(
                    # The usual input-sanitization stuff from MySQLdb
                    # (like `%(var)s`) doesn't seem to be supported for a schema
                    # related command like this. So we just have an f-string.
                    f"DROP TABLE {table_name}",
                )

        # Delete columns we don't need.

        cursor.execute("DESC phpbb_users")
        all_user_columns = set([
            result[0] for result in cursor.fetchall()
        ])

        user_columns_to_keep = {
            'user_id',
            'username',
            # For the PAL setting. Unfortunately this field can also have
            # personal info though.
            'user_interests',
        }
        user_columns_to_delete = all_user_columns - user_columns_to_keep

        for user_column in user_columns_to_delete:
            cursor.execute(
                f"ALTER TABLE phpbb_users DROP COLUMN {user_column}",
            )

        post_columns_to_delete = {
            # The only sensitive PII in the posts table: IP addresses.
            'poster_ip',
        }

        for post_column in post_columns_to_delete:
            cursor.execute(
                f"ALTER TABLE phpbb_posts DROP COLUMN {post_column}",
            )

        # Delete rows we don't need.

        cursor.execute(
            f"DELETE FROM phpbb_posts WHERE post_id NOT IN("
            + ','.join([str(post_id) for post_id in POST_IDS_TO_SAVE])
            + f")",
        )
        # Unlike the schema changes, the data deletion won't be saved unless
        # we commit.
        mysql_conn.commit()

        # Redump.

        if options.get('reduced_backup_path'):
            reduced_backup_path = options['reduced_backup_path']
        else:
            # With a name like myfile.sql.gz, Path.stem drops .gz but not .sql,
            # resulting in myfile.sql. We'd like to drop both, resulting in
            # myfile. So we split on . manually.
            stem = raw_backup_path.name.split('.')[0]
            reduced_backup_path = (
                raw_backup_path.parent / (stem + '_reduced.sql'))

        with open(reduced_backup_path, 'w+b') as reduced_sql_f:
            proc = subprocess.Popen(
                ['mysqldump', '-u', 'root', '--databases', temp_database_name],
                stdout=reduced_sql_f,
            )
            # Wait for it to finish before moving on.
            proc.wait()

        # Re-gzipping would be nice, but a pain to do this in a way that
        # doesn't 1) run out of memory on large files, or 2) rely on platform
        # specific commands to do the gzipping.
        # So we just leave the output uncompressed.

        # Delete the temporary database.
        cursor.execute(
            f"DROP DATABASE {temp_database_name}",
        )
