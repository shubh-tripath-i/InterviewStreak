from django.shortcuts import render
from django.http import JsonResponse


def index(request):
    context = {
    }
    return render(request, 'migpt/index.html', context)

def call_llm(request):
    data = {
        'success': True,
        'message': "Hello there!"
    }
    return JsonResponse(data)