# Generated by Django 4.0 on 2022-03-19 11:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('filter_groups', '0002_filtergroup_game_filtergroup_order_in_game_and_more'),
        ('chart_types', '0002_alter_charttype_filter_groups_delete_ctfg'),
    ]

    operations = [
        migrations.AlterField(
            model_name='charttype',
            name='filter_groups',
            field=models.ManyToManyField(related_name='chart_types', to='filter_groups.FilterGroup'),
        ),
    ]
