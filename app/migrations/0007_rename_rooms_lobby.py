# Generated by Django 3.2.18 on 2023-04-22 11:21

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app', '0006_alter_rooms_gamejson'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Rooms',
            new_name='Lobby',
        ),
    ]
