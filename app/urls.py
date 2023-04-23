from django.contrib import admin
from django.urls import path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from .views import *

app_name = 'app'

urlpatterns = [ 
    path('slotlist/', SlotList.as_view(), name='slotlist'),
    path('reqForROOM/<str:capacity>',ReqForROOM.as_view(),name='reqForROOM'),
    path('leave/<str:room_name>', LeaveRoomView.as_view(), name="leave_room"),
    path('<str:room_name>/',WaitingRoom.as_view(),name='room'),
    path('InGame/<str:room_name>/',InGame.as_view(),name='InGame'),
    path('startingGame/<str:room_name>/',StartingGame.as_view(),name='startingGame'),
]
urlpatterns += staticfiles_urlpatterns()