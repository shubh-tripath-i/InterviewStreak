from django.http import JsonResponse
from migpt import utils
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import SignUpForm


def index(request):
    context = {
    }
    return render(request, 'migpt/index.html', context)


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
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