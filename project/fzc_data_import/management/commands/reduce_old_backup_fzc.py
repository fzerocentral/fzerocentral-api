from io import StringIO
import os
from pathlib import Path
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand
import MySQLdb

from ...utils import gzip_readable_stream, write_gzip


POSSIBLE_INPUT_DATABASE_NAMES = [
    'fzero',
    'fileand6_mfoforums',
]


def replace_database_name(line):
    for name in POSSIBLE_INPUT_DATABASE_NAMES:
        if name in line:
            temp_name = f'temp_{name}_reduced_version'
            return line.replace(name, temp_name), temp_name
    raise ValueError(
        f"Couldn't find an expected database name in this line: {line}")


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
            'input_backup_path',
            type=str,
            help="gzipped full backup file from old FZC")

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

        input_backup_path = Path(options['input_backup_path'])
        temp_database_name = None
        with (
            gzip_readable_stream(options['input_backup_path'])
            as old_sql_stream
        ):
            # Change database name of the backup stream to
            # something unlikely to cause conflicts or confusion.
            new_sql_stream = StringIO()
            for line in old_sql_stream:
                # These are the two lines of the backup stream where we
                # need to change the database name, to define where the
                # data will be restored to.
                if (
                    line.startswith("CREATE DATABASE")
                    or line.startswith("USE `")
                ):
                    line, temp_database_name = replace_database_name(line)
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
        }
        tables_to_drop = all_tables - tables_to_keep

        for table_name in tables_to_drop:
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

        # Redump and re-gzip.

        new_dump_sql = subprocess.check_output(
            ['mysqldump', '-u', 'root', '--databases', temp_database_name],
            text=True,
            encoding='utf-8',
        )

        output_backup_path = (
            input_backup_path.parent
            / (input_backup_path.stem + '_reduced.sql.gz'))
        write_gzip(
            filepath=output_backup_path, content_bytes=new_dump_sql.encode())

        # Delete the temporary database.
        cursor.execute(
            f"DROP DATABASE {temp_database_name}",
        )
