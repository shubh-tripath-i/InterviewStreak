from django.urls import path
from . import views

app_name = 'migpt'

urlpatterns = [
    path('', views.index, name='index'),
    path('call_llm/', views.call_llm, name="call_llm"),
    path('accounts/signup/', views.signup, name='signup'),
    path('profile/', views.view_profile, name='view_profile'),
    path('profile/edit', views.update_profile, name='update_profile'),
]