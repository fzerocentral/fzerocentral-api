# Generated by Django 4.0 on 2022-05-31 00:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('forum_old_topics', '0001_initial'),
        ('forum_old_users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=500)),
                ('text', models.CharField(max_length=1000000)),
                ('time', models.DateTimeField()),
                ('username', models.CharField(max_length=30)),
                ('poster', models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, to='forum_old_users.user')),
                ('topic', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='forum_old_topics.topic')),
            ],
        ),
    ]
