# Generated by Django 4.0.4 on 2022-05-13 11:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chart_tags', '0002_remove_charttag_short_name_and_more'),
        ('ladders', '0002_laddercharttag'),
    ]

    operations = [
        migrations.AlterField(
            model_name='laddercharttag',
            name='chart_tag',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ladder_chart_tags', to='chart_tags.charttag'),
        ),
        migrations.AlterField(
            model_name='laddercharttag',
            name='ladder',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ladder_chart_tags', to='ladders.ladder'),
        ),
    ]
