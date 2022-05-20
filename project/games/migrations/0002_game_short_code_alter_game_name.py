# Generated by Django 4.0.4 on 2022-05-09 11:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='short_code',
            field=models.CharField(default='', max_length=20, unique=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='game',
            name='name',
            field=models.CharField(max_length=200, unique=True),
        ),
    ]