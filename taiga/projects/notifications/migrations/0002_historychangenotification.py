# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0004_historyentry_is_hidden'),
        ('projects', '0005_membership_invitation_extra_text'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoryChangeNotification',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('key', models.CharField(max_length=255, editable=False, unique=True)),
                ('created_datetime', models.DateTimeField(auto_now_add=True, verbose_name='created date time')),
                ('updated_datetime', models.DateTimeField(auto_now_add=True, verbose_name='updated date time')),
                ('history_type', models.SmallIntegerField(choices=[(1, 'Change'), (2, 'Create'), (3, 'Delete')])),
                ('history_entries', models.ManyToManyField(null=True, related_name='+', to='history.HistoryEntry', verbose_name='history entries', blank=True)),
                ('notify_users', models.ManyToManyField(null=True, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='notify users', blank=True)),
                ('owner', models.ForeignKey(related_name='+', verbose_name='owner', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(related_name='+', verbose_name='project', to='projects.Project')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
