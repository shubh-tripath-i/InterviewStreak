from django.urls import path
from . import views

app_name = 'migpt'

urlpatterns = [
    path('', views.index, name='index'),
    path('call_llm/',views.call_llm,name="call_llm")
]