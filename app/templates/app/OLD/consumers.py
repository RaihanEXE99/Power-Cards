
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
    async def whosTurn(self):
        user = self.scope['user']
        obj = await sync_to_async(Lobby.objects.filter(users_m=user,room_name=self.room_name).first)()
        for ins in obj.gameJson["players"]:  
            if ins['myTurn']==True:
                return ins['username']
    async def getMe(self):
        user = self.scope['user']
        exist = await sync_to_async(Lobby.objects.filter(users_m=user,room_name=self.room_name).first)()
        players = exist.gameJson["players"]
        for player in players:
            if player["username"]==user.username:
                return player
    # async def playerPoints(self):
    #     user = self.scope['user']
    #     exist = await sync_to_async(Lobby.objects.filter(users_m=user,room_name=self.room_name).first)()
    #     players = exist.gameJson["players"]
    #     points = []
    #     for player in players:
    #         points.append({
    #             "username":player["username"],
    #             "points":player["points"]
    #         })
    #     return points
                

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
            whosTurn = await self.whosTurn()
            me = await self.getMe()
            
            dashboard = []
            for player in obj.gameJson["players"]:
                dashboard.append({"username":player["username"],"points":player["points"]})
            await self.send(json.dumps({
                "type":"init" if obj.status!="finished" else obj.status,
                "whosTurn":whosTurn,
                "myCards":me["cards"],
                "cardPlaced":obj.gameJson["cardPlaced"],
                "myTurn":["True" if me["myTurn"] else "False"],
                "points":me["points"],
                "dashboard":dashboard
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
        me = await self.getMe()
        if(data['type']=='sv'):
            myCards = me["cards"]
            lobby.gameJson["cardPlaced"][me["index"]]=me["cards"][sv]
            myCards.pop(sv)
            lobby.gameJson["players"][me["index"]]["cards"]=myCards
            for i in range(lobby.capacity):
                if lobby.gameJson["players"][i]["myTurn"]==True and (i<lobby.capacity-1):
                    lobby.gameJson["players"][i]["myTurn"]=False
                    lobby.gameJson["players"][i+1]["myTurn"]=True
                    break
                elif lobby.gameJson["players"][i]["myTurn"]==True and i>=lobby.capacity-1:
                    lobby.gameJson["players"][i]["myTurn"]=False
                    lobby.gameJson["players"][0]["myTurn"]=True
                    break
                
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
        isBothPlaced =True if -1 not in obj.gameJson["cardPlaced"] else False
        whosTurn = await self.whosTurn()
        me = await self.getMe()
        
        if isBothPlaced:
            def has_duplicates(lst):
                return len(lst) != len(set(lst))
            if has_duplicates(obj.gameJson["cardPlaced"]):
                pass
            else:
                givePointToIndex=obj.gameJson["cardPlaced"].index(max(obj.gameJson["cardPlaced"]))
                obj.gameJson["players"][givePointToIndex]["points"] += 1
                await sync_to_async(obj.save,thread_sensitive=True)()
            dashboard = []
            for player in obj.gameJson["players"]:
                dashboard.append({"username":player["username"],"points":player["points"]})
            await self.send(json.dumps({
                "type":"bothPlaced" if obj.status!="finished" else obj.status,
                "whosTurn":whosTurn,
                "myCards":me["cards"],
                "cardPlaced":obj.gameJson["cardPlaced"],
                "myTurn":["True" if me["myTurn"] else "False"],
                "dashboard":dashboard
            }))
            obj.gameJson["cardPlaced"] = [-1 for _ in range(obj.capacity)]
            await sync_to_async(obj.save,thread_sensitive=True)()

            sizeList = []
            for player in obj.gameJson["players"]:
                sizeList.append(len(player["cards"]))

            if all(x == 0 for x in sizeList):
                obj.gameJson["status"] = "finished"
                obj.status = "finished"
                await sync_to_async(obj.save,thread_sensitive=True)()
                await self.send(json.dumps({
                "type":"finished",
                "whosTurn":whosTurn,
                "myCards":me["cards"],
                "cardPlaced":obj.gameJson["cardPlaced"],
                "myTurn":["True" if me["myTurn"] else "False"],
                "dashboard":dashboard
            }))
        else:
            dashboard = []
            for player in obj.gameJson["players"]:
                dashboard.append({"username":player["username"],"points":player["points"]})
            await self.send(json.dumps({
                "type":"play" if obj.status!="finished" else obj.status,
                "whosTurn":whosTurn,
                "myCards":me["cards"],
                "cardPlaced":obj.gameJson["cardPlaced"],
                "myTurn":["True" if me["myTurn"] else "False"],
                "dashboard":dashboard
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