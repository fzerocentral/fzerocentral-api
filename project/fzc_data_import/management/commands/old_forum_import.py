import datetime
import getpass

from django.core.management.base import BaseCommand
import MySQLdb

from forum_old.categories.models import Category
from forum_old.forums.models import Forum
from forum_old.posts.models import Post
from forum_old.topics.models import Topic
from forum_old.users.models import User
from ...utils import convert_text


class Command(BaseCommand):
    help = """
    Import forum data from the old FZC database.
    
    Example usage:
    python manage.py old_forum_import localhost 3306 fzc_php root
    """

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
            help="Clear all existing old-forum data in the Django DB")

    def handle(self, *args, **options):

        # Connect to the MySQL DB
        password = getpass.getpass(
            f"Enter password for MySQL user {options['mysql_user']}: ")
        mysql_conn = MySQLdb.connect(
            host=options['mysql_host'], port=options['mysql_port'],
            user=options['mysql_user'], passwd=password,
            db=options['mysql_dbname'], charset='utf8')
        mysql_cur = mysql_conn.cursor(MySQLdb.cursors.DictCursor)

        if options['clear_existing']:
            self.stdout.write("Clearing existing old-forum data...")
            Post.objects.all().delete()
            Topic.objects.all().delete()
            Forum.objects.all().delete()
            Category.objects.all().delete()
            User.objects.all().delete()
            self.stdout.write("Done")

        start_time = datetime.datetime.now()

        # Get Users from phpBB and create in Django. Only create if they
        # have at least one post.
        # Note that the `phpbb_posts` field is not reliable for this;
        # 1612 users have user_posts > 0, while the below query only gets
        # 790 users.

        mysql_cur.execute(
            "SELECT user_id, username FROM phpbb_users"
            " WHERE exists(SELECT 1 FROM phpbb_posts"
            " WHERE phpbb_posts.poster_id = phpbb_users.user_id);")

        users = []
        for d in mysql_cur.fetchall():
            users.append(User(
                id=d['user_id'],
                username=convert_text(d['username']),
            ))
        User.objects.bulk_create(users)

        # Get Categories from phpBB and create in Django.

        mysql_cur.execute(
            "SELECT cat_id, cat_title, cat_order"
            " FROM phpbb_categories;")

        categories = []
        for d in mysql_cur.fetchall():
            categories.append(Category(
                id=d['cat_id'],
                title=convert_text(d['cat_title']),
                order=d['cat_order'],
            ))
        Category.objects.bulk_create(categories)

        # Get Forums from phpBB and create in Django.
        # auth_view = 0 means the forum's publicly viewable. Staff-only is 2.

        mysql_cur.execute(
            "SELECT forum_id, cat_id, forum_name, forum_desc, forum_order"
            " FROM phpbb_forums"
            " WHERE auth_view = 0;")

        forums = []
        for d in mysql_cur.fetchall():
            forums.append(Forum(
                id=d['forum_id'],
                category_id=d['cat_id'],
                name=convert_text(d['forum_name']),
                description=convert_text(d['forum_desc']),
                order=d['forum_order'],
            ))
        Forum.objects.bulk_create(forums)

        # Get Topics from phpBB and create in Django.

        mysql_cur.execute(
            "SELECT t.topic_id, t.forum_id, t.topic_title"
            " FROM phpbb_topics as t"
            " JOIN phpbb_forums as f ON t.forum_id = f.forum_id"
            " WHERE f.auth_view = 0;")

        topics = []
        for d in mysql_cur.fetchall():
            if d['topic_id'] == 13928:
                # Spammer's topic which wasn't purged
                continue
            topics.append(Topic(
                id=d['topic_id'],
                forum_id=d['forum_id'],
                title=convert_text(d['topic_title']),
            ))
        Topic.objects.bulk_create(topics)

        # Get Posts from phpBB and create in Django.
        # Post info is in two tables, phpbb_posts and phpbb_posts_text.

        mysql_cur.execute(
            "SELECT p.post_id, p.topic_id, p.poster_id, p.post_time,"
            " p.post_username, tx.post_subject, tx.post_text"
            " FROM phpbb_posts as p"
            " JOIN phpbb_posts_text as tx ON p.post_id = tx.post_id"
            " JOIN phpbb_topics as t ON p.topic_id = t.topic_id"
            " JOIN phpbb_forums as f ON t.forum_id = f.forum_id"
            " WHERE f.auth_view = 0;")

        posts = []
        for d in mysql_cur.fetchall():
            if d['poster_id'] == -1:
                # Guest post or deleted user
                poster_id = None
            elif d['poster_id'] in [34533]:
                # Deleted spammer, but posts weren't purged
                continue
            else:
                poster_id = d['poster_id']
            posts.append(Post(
                id=d['post_id'],
                topic_id=d['topic_id'],
                poster_id=poster_id,
                time=datetime.datetime.fromtimestamp(
                    d['post_time'], tz=datetime.timezone.utc),
                username=convert_text(d['post_username']),
                subject=convert_text(d['post_subject']),
                raw_text=convert_text(d['post_text']),
            ))
        Post.objects.bulk_create(posts)

        end_time = datetime.datetime.now()

        # Print stats.

        self.stdout.write(
            f"""
            -----
            Old-forum import: Overall counts
            -----
            {User.objects.all().count()} users
            {Category.objects.all().count()} categories
            {Forum.objects.all().count()} forums
            {Topic.objects.all().count()} topics
            {Post.objects.all().count()} posts
            Time taken to import: {end_time - start_time}
            """
        )
