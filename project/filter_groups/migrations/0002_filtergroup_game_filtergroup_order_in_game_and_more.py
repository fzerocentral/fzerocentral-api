# Generated by Django 4.0 on 2022-03-19 03:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0001_initial'),
        ('filter_groups', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='filtergroup',
            name='game',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='games.game'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='filtergroup',
            name='order_in_game',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='filtergroup',
            name='show_by_default',
            field=models.BooleanField(default=True),
        ),
    ]
