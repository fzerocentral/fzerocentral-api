# Generated by Django 4.0 on 2022-04-21 22:43

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ladders', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LadderChartTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight', models.DecimalField(decimal_places=3, default=Decimal('1'), max_digits=4, validators=[django.core.validators.MaxValueValidator(Decimal('1')), django.core.validators.MinValueValidator(Decimal('0'))])),
                ('chart_tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chart_tags.charttag')),
                ('ladder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ladders.ladder')),
            ],
        ),
    ]
