# Generated by Django 4.0 on 2022-04-23 23:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chart_types', '0003_alter_charttype_filter_groups'),
        ('chart_tags', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='charttag',
            name='short_name',
        ),
        migrations.AddField(
            model_name='charttag',
            name='primary_chart_type',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.RESTRICT, to='chart_types.charttype'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='charttag',
            name='total_name',
            field=models.CharField(default=1, max_length=50),
            preserve_default=False,
        ),
    ]
