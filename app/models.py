from django.db import models
from django.contrib.auth.models import User, AbstractUser
# import datetime
# from dateutil.parser import parse
# import maya
# import uuid
# from .utils import generate_ref_code

# Create your models here.
def defaultGameJSON():return {"status":"waiting"}

class Lobby(models.Model):
    room_name = models.CharField(max_length=100)
    capacity = models.IntegerField(default=2)
    users_m = models.ManyToManyField(User, related_name="user_m")
    status = models.CharField(max_length=20,default="waiting")
    gameJson = models.JSONField(default=defaultGameJSON)
    def __str__(self):
        return str(self.room_name)
    objects = models.Manager()
    class meta:
        managed = True
        db_table = 'Lobby'

