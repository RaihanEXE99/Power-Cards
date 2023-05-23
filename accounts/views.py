from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required

# Create your views here.
def sign_up(request):
    if request.method == "POST":
        req = request.POST
        username = req['username']
        password1 = req['password1']
        password2 = req['password2']
        if password1!=password2:
            print("Password and confirm password isn't same!")
        else:
            try:
                user = User.objects.get(username=username)
                print(f"Username {user} already exist!")
            except User.DoesNotExist:
                User.objects.create_user(username=req['username'],password=req['password1'])
                return redirect('/accounts/login')

    return render(request,'registration/sign_up.html')