from django.urls import path, re_path
from . import views
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView, PasswordChangeView, PasswordChangeDoneView

app_name = 'migpt'

urlpatterns = [
    path('', views.index, name='index'),
    path('accounts/signup/', views.signup, name='signup'),
    path('profile/', views.view_profile, name='view_profile'),
    path('profile/edit', views.update_profile, name='update_profile'),
    path('activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/', views.verify_email, name='verify_email'),
    path('get_question/', views.get_question, name="get_question"),
    path('create-interview-session/', views.create_interview_session, name='create_interview_session'),
    path('start-interview/', views.start_interview, name='start_interview'),
    path('save-answer/', views.save_answer, name='save_answer'),
    path('end-interview/', views.end_interview, name='end_interview'),
    path('accounts/password_change/', PasswordChangeView.as_view(template_name='migpt/password_change.html'), name='password_change'),
    path('accounts/password_change/done/', PasswordChangeDoneView.as_view(template_name='migpt/password_change_done.html'), name='password_change_done'),
    path('accounts/password_reset/', views.CustomPasswordResetView.as_view(template_name='migpt/password_reset_form.html'), name='password_reset'),
    path('accounts/password_reset/done/', PasswordResetDoneView.as_view(template_name='migpt/password_reset_done.html'), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='migpt/password_reset_confirm.html'), name='password_reset_confirm'),
    path('accounts/reset/done/', PasswordResetCompleteView.as_view(template_name='migpt/password_reset_complete.html'), name='password_reset_complete'),
    path('display-interview-result/', views.display_result, name='display_result'),
    path('get-answer-automatically/', views.get_answer_automatically, name='get_answer_automatically'),
    path('check-review-status/', views.check_review_status, name="check_review_status")
]
