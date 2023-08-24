from django.http import JsonResponse
from migpt import utils
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .forms import SignUpForm, UserProfileForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from migpt import models


def index(request):
    context = {
    }
    return render(request, 'migpt/index.html', context)


@login_required
def view_profile(request):
    user = User.objects.filter(id=request.user.id)[0]
    context = {"name": user.first_name + user.last_name
               }
    return render(request, 'migpt/view_profile.html', context)


@login_required
def update_profile(request):
    userprofile = models.UserProfile.objects.filter(user=request.user)[0]
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=userprofile)
        if form.is_valid():
            print("is valid called")
            form.save()
            return redirect("migpt:update_profile")
    else:
        form = UserProfileForm(instance=userprofile)
    return render(request, 'migpt/edit_profile.html', {'form': form})


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("migpt:index")
    else:
        form = SignUpForm()
    return render(request, 'migpt/signup.html', {'form': form})


def call_llm(request):
    chain = utils.make_chain()
    data = {
        'success': True,
        'message': "Hello there!"
    }
    return JsonResponse(data)