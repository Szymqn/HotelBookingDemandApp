from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm, SignUpForm


def log_in_page(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = LoginForm()

    return render(request, 'auth/log_in.html', {'form': form})


def sign_up_page(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user = authenticate(username=user.username, password=form.cleaned_data['password'])
            if user is not None:
                login(request, user)
                messages.success(request, "Account created and logged in successfully!")
                return redirect('dashboard')
    else:
        form = SignUpForm()

    return render(request, 'auth/sign_up.html', {'form': form})



def log_out_page(request):
    logout(request)
    return redirect('dashboard')
