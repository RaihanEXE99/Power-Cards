from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import *
import random,math,string
from django.views import View
from django.utils.decorators import method_decorator
from django.db.models import Q

from allauth.socialaccount.models import SocialAccount
ERROR = JsonResponse({
    "RES" : "ERROR"
})

class HomeView(View):
    def get(self, request, *args, **kwargs):
        context = {
            "result":"DEBUG",
            "username": request.user,
        }
        return render(request, 'app/index.html', context)
    
class SlotList(LoginRequiredMixin,View):
    def if_inLobby_then_redirect(self, request, *args, **kwargs):
        user = request.user
        b_alreadyInGame = Lobby.objects.filter(users_m=user)
        if b_alreadyInGame:
            return b_alreadyInGame[0].room_name
        else:
            return None
    def get(self, request, *args, **kwargs):
        room = self.if_inLobby_then_redirect(request)
        if room:
            return redirect('app:room', room_name=room)
        else:
            return render(request, 'app/slotlist.html', {})

class ReqForROOM(LoginRequiredMixin,View):
    def roomGEN(self, size=30, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def get(self, request, capacity, *args, **kwargs):
        exist = Lobby.objects.filter(capacity=capacity, status="waiting")
        if exist:
            room = exist[0]
            me = request.user
            alreadyIN = [user for user in room.users_m.all() if user.username == me.username]
            if alreadyIN:
                return redirect('app:room', room_name=room.room_name)
            if room.users_m.count() < room.capacity:
                room.users_m.add(me)
                return redirect('app:room', room_name=room.room_name)
            else:
                return HttpResponse("Room is full")
        else:
            alreadyINGame = Lobby.objects.filter(users_m=request.user.id).exclude(status="finished")
            if alreadyINGame:
                return redirect("app:InGame",room_name=alreadyINGame[0].room_name)
            me = request.user
            createRoom = Lobby.objects.create(
                room_name=self.roomGEN(),
                capacity=capacity
            )
            createRoom.users_m.add(me)
            return redirect('app:room', room_name=createRoom.room_name)

class WaitingRoom(LoginRequiredMixin,View):
    def get(self, request, room_name, *args, **kwargs):
        exist = get_object_or_404(Lobby, room_name=room_name)
        if exist.status == "started":
            return redirect("app:InGame",room_name=exist.room_name)
        user_valid = request.user
        is_valid = exist.users_m.filter(username=user_valid.username).exists()
        active_counter = exist.users_m.count()
        if is_valid:
            return render(request, 'app/room.html', {
                'room_name': room_name,
                'active_counter': active_counter,
                'capacity': exist.capacity,
            })
        else:
            return ERROR

class StartingGame(LoginRequiredMixin,View): 
    def initiateGame(self,lobby):
        def randomCardList(n):return [random.randint(1, 100) for _ in range(n)]
        playersUsername=[user.username for user in lobby.users_m.all()]
        players = []
        count = 0
        for username in playersUsername:
            players.append({
                "pid":User.objects.get(username=username).id,
                "index":count,
                "username":username,
                "cards":randomCardList(10),
                "myTurn":True if count==0 else False,
                "points":0,
            })
            count+=1
        total_players = len(playersUsername)
        gameJson = {
            "status":"in-game",
            "room_name":lobby.room_name,
            "total_players":total_players,
            "players":players,
            "cardPlaced":[-1 for _ in range(total_players)]
        }
        print(gameJson)
        return gameJson
    def get(self, request, room_name, *args, **kwargs):
        exist = get_object_or_404(Lobby,room_name=room_name)
        # EXIST
        me = request.user
        isValid = [user for user in exist.users_m.all() if user.username == me.username]
        activeCouter = exist.users_m.all().count()
        userlist = list(user.username for user in exist.users_m.all())
        if exist.status == "waiting" and exist.capacity == activeCouter and isValid:
            exist.gameJson = self.initiateGame(exist)
            exist.status="started"
            exist.save()
            return redirect('app:InGame',room_name = room_name)
        elif exist.status == "started" and exist.capacity == activeCouter and isValid:
            return redirect('app:InGame',room_name = room_name)
        # Have To check Next  
        elif exist.status == "FINISHED" and exist.capacity == activeCouter and isValid:
            exist.showed.add(me)
            isShownToYou = [user for user in exist.showed.all() if user.username == me.username]
            if not isShownToYou:
                exist.showed.add(me)
                exist.save()
                countShow = sum([1 for user in exist.showed.all()])
                # userlist = [user.username for user in exist.users_m.all()]
                if countShow == activeCouter:
                    exist.delete()
                return JsonResponse({
                    'room_name' : room_name,
                    'userlist' : userlist,
                    'social_accounts':userListToSocialAccounts(userlist)
                })
            else:
                ERROR
        else:
            return ERROR

class InGame(LoginRequiredMixin, View):
    def get(self, request, room_name, *args, **kwargs):
        exist = get_object_or_404(Lobby, room_name=room_name,status__in=["started","finished"],gameJson__status__in=["in-game", "finished"])
        userlist = [user.username for user in exist.users_m.all()]
        # 
        # 
        return render(request,'app/InGame.html',{
            'room_name' : room_name,
            'userlist' : userlist,
            'social_accounts':userListToSocialAccounts(userlist)
        })

def userListToSocialAccounts(userlist):
    social_users = User.objects.filter(username__in=userlist)
    return SocialAccount.objects.filter(user__in=social_users)

class LeaveRoomView(LoginRequiredMixin, View):
    def get(self, request, room_name, *args, **kwargs):
        exist = Lobby.objects.get(room_name=room_name, status="waiting")
        if not exist:
            return render(request, 'app/error.html')
        userValid = request.user
        isValid = [user for user in exist.users_m.all() if user.username == userValid.username]
        if isValid:
            exist.users_m.remove(userValid)
            exist.save()
            return redirect("app:HomeView")
        else:
            return ERROR

# @login_required
# def leave_room(request,room_name):
#     exist =  Lobby.objects.get(room_name=room_name,status = "waiting")
#     if not exist:
#         return ERROR
#     userValid = User.objects.get(id=request.user.id)
#     isValid = [user for user in exist.users_m.all() if user.username == userValid.username]
#     if isValid:
#         exist.users_m.remove(userValid)
#         exist.save()
#         return render(request,'app/index.html')
#     else:
#         return ERROR


# def roomGEN(size=30, chars=string.ascii_uppercase + string.digits):
#     return ''.join(random.choice(chars) for _ in range(size))


# @login_required
# def reqForROOM(request,capacity):
#     exist =  Lobby.objects.filter(status = "waiting")
#     if exist:
#         room = exist[0]
#         me = User.objects.get(id=request.user.id)    
#         active_users = sum([1 for user in room.users_m.all()])
#         alreadyIN = [user for user in room.users_m.all() if user.username == me.username]
#         if alreadyIN:
#             return redirect('app:room',room_name = room.room_name)
#         if active_users < room.capacity:
#             room.users_m.add(me)
#             return redirect('app:room',room_name = room.room_name)
#         else:
#             return ERROR
#     else:
#         me = User.objects.get(id=request.user.id)
#         createRoom = Lobby(
#             room_name = roomGEN(),
#             capacity = capacity
#         )
#         createRoom.save()
#         createRoom.users_m.add(me)
#         return redirect('app:room',room_name = createRoom.room_name)

# @login_required
# def cardgame(request,room_name, *args, **kwargs):
#     exist =  Lobby.objects.get(room_name=room_name)
#     if not exist:
#         return ERROR
#     # EXIST
#     userValid = User.objects.get(id=request.user.id)
#     isValid = [user for user in exist.users_m.all() if user.username == userValid.username]
#     activeCouter = sum([1 for user in exist.users_m.all()])
    
#     userlist = [user.username for user in exist.users_m.all()]
#     if exist.status == "waiting" and exist.capacity == activeCouter and isValid:    
#         return redirect('app:InGame',room_name = room_name)
#     # Have To check Next  
#     elif exist.status == "FINISHED" and exist.capacity == activeCouter and isValid:
#         exist.showed.add(userValid)
#         isShownToYou = [user for user in exist.showed.all() if user.username == userValid.username]
#         if not isShownToYou:
#             exist.showed.add(userValid)
#             exist.save()
#             countShow = sum([1 for user in exist.showed.all()])
#             # userlist = [user.username for user in exist.users_m.all()]
#             if countShow == activeCouter:
#                 exist.delete()
#             return JsonResponse({
#                 'room_name' : room_name,
#                 'userlist' : userlist,
#             })
#         else:
#             ERROR
#     else:
#         return ERROR