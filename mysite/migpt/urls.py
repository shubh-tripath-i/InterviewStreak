from django.urls import path, re_path
from . import views

app_name = 'migpt'

urlpatterns = [
    path('', views.index, name='index'),
    path('get_question/', views.get_question, name="get_question"),
    path('accounts/signup/', views.signup, name='signup'),
    path('profile/', views.view_profile, name='view_profile'),
    path('profile/edit', views.update_profile, name='update_profile'),
    re_path('activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/', views.verify_email, name='verify_email'),
    path('create-interview-session/', views.create_interview_session, name='create_interview_session'),
    path('start-interview/', views.start_interview, name='start_interview'),
    path('save-answer/', views.save_answer, name='save_answer')
]
