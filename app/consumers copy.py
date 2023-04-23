
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async

from channels.db import database_sync_to_async
from .models import Lobby


class WaitingLobbyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'room_'+self.room_name

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        room_name = text_data_json['room_name']
        active_counter = text_data_json['active_counter']

        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chatroom_message',
                'room_name': room_name,
                'active_counter': active_counter,
            }
        )

    async def chatroom_message(self, event):
        room_name = event['room_name']
        active_counter = event['active_counter']

        await self.send(text_data=json.dumps({
            'room_name': room_name,
            'active_counter': active_counter,
        }))
    pass


class InGameConsumer(AsyncWebsocketConsumer):

    async def checkUserValidity(self):
        user = self.scope['user']
        exist = await sync_to_async(Lobby.objects.filter(users_m=user,room_name=self.room_name).first)()
        if exist:return exist
        else:return False
    async def whosTurn(self,obj):
        return obj.gameJson['turn']


    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'room_'+self.room_name

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        obj = await self.checkUserValidity()
        if obj:
            await self.accept()
            turn = await self.whosTurn(obj)
            myIndex = obj.gameJson["players"].index(self.scope['user'].username)
            print(obj.gameJson["cardPlaced"])
            await self.send(json.dumps({
                "type":"init",
                "turn":turn,
                "whosTurn":obj.gameJson['players'][turn],
                "myCards":obj.gameJson["cards"][myIndex],
                "cardPlaced":obj.gameJson["cardPlaced"],
                "myTurn":["True" if obj.gameJson['players'][turn]==self.scope['user'].username else "False"],
                "points":obj.gameJson["points"]
            }))
        else:pass

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        user = self.scope['user']
        data = json.loads(text_data)
        sv = int(data['sv'])
        lobby = await sync_to_async(Lobby.objects.filter(users_m=user,room_name=self.room_name).first)()
        gameJson = lobby.gameJson
        myIndex = lobby.gameJson["players"].index(self.scope['user'].username)
        if(data['type']=='sv'):
            # print(gameJson["cards"][myIndex][sv])
            myCards = gameJson["cards"][myIndex]
            lobby.gameJson["cardPlaced"][myIndex]=gameJson["cards"][myIndex][sv]
            myCards.pop(sv)
            lobby.gameJson["cards"][myIndex]=myCards
            lobby.gameJson["turn"]=(lobby.gameJson["turn"]+1)%(lobby.gameJson["total_players"])
            print(lobby.gameJson["turn"])
            await sync_to_async(lobby.save,thread_sensitive=True)()
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'lobbyUpdate',
                    # 'message': 'Hello, world!'
                }
            )
        else:
            print("Failed-recive-sv")

    async def lobbyUpdate(self, event):
        # message = event["message"]
        user = self.scope['user']
        obj = await sync_to_async(Lobby.objects.filter(users_m=user,room_name=self.room_name).first)()
        turn = await self.whosTurn(obj)
        myIndex = obj.gameJson["players"].index(self.scope['user'].username)
        await self.send(json.dumps({
            "type":"play",
            "turn":turn,
            "whosTurn":obj.gameJson['players'][turn],
            "myCards":obj.gameJson["cards"][myIndex],
            "cardPlaced":obj.gameJson["cardPlaced"],
            "myTurn":["True" if obj.gameJson['players'][turn]==self.scope['user'].username else "False"]
        }))
    pass




    # Iterate SELF
    # for key, value in vars(self).items():
    #     print(f"{key}: {value}")


    # # @database_sync_to_async
    # def save_data_to_database(self, data):
    #     # Perform database operation
    #     user = self.scope['user']
    #     print(user)
    #     # obj = Lobby.objects.get(name=data['name'], value=data['value'])
    #     # return {'id': obj.id, 'name': obj.name, 'value': obj.value}