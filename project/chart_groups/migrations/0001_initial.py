# Generated by Django 4.0 on 2021-12-22 11:26

from django.db import migrations, models
import django.db.models.deletion
import django.db.models.expressions


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('games', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChartGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('order_in_parent', models.IntegerField()),
                ('show_charts_together', models.BooleanField(default=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='games.game')),
                ('parent_group', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='child_groups', to='chart_groups.chartgroup')),
            ],
        ),
        migrations.AddConstraint(
            model_name='chartgroup',
            constraint=models.UniqueConstraint(django.db.models.expressions.F('parent_group'), django.db.models.expressions.F('order_in_parent'), name='unique_chartgroup_parent_order'),
        ),
    ]
