from django.urls import path, re_path
from . import views

app_name = 'migpt'

urlpatterns = [
    path('', views.index, name='index'),
    path('call_llm/', views.call_llm, name="call_llm"),
    path('accounts/signup/', views.signup, name='signup'),
    path('profile/', views.view_profile, name='view_profile'),
    path('profile/edit', views.update_profile, name='update_profile'),
    re_path('activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/', views.verify_email, name='verify_email'),
]