# Generated by Django 4.0 on 2022-06-19 05:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('forum_old_posts', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='Post', old_name='text', new_name='raw_text')
    ]
