# Generated by Django 3.2.18 on 2023-04-14 19:35

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app', '0002_alter_rooms_total'),
    ]

    operations = [
        migrations.AddField(
            model_name='rooms',
            name='showed',
            field=models.ManyToManyField(blank=True, related_name='showed', to=settings.AUTH_USER_MODEL),
        ),
    ]
