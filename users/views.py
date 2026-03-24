from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .models import CustomUser


def log_in_page(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Invalid Username')
            return redirect('log_in')

        user = authenticate(username=username, password=password)

        if user is None:
            messages.error(request, "Invalid Password")
            return redirect('log_in')
        else:
            login(request, user)
            return redirect('dashboard')

    return render(request, 'user/log_in.html')


def sign_up_page(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = CustomUser.objects.filter(username=username)

        if user.exists():
            messages.info(request, "Username already taken!")
            return redirect('sign_up')

        user = CustomUser.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username
        )

        user.set_password(password)
        user.save()

        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            messages.info(request, "Account created and logged in successfully!")
            return redirect('dashboard')

    return render(request, 'user/sign_up.html')


def log_out_page(request):
    logout(request)
    return redirect('dashboard')
