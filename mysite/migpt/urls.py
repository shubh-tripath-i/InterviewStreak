from django.urls import path
from . import views
from allauth.account.views import (
    LoginView,
    LogoutView,
    PasswordResetView,
)
from django.contrib.sitemaps.views import sitemap
from sitemaps import StaticViewSitemap


sitemaps = {
    'static': StaticViewSitemap,
}

app_name = 'migpt'

urlpatterns = [
    path('', views.index, name='index'),
    path('accounts/signup/', views.signup, name='signup'),
    path('accounts/login/', views.CustomLoginView.as_view(), name='login'),
    path('accounts/logout/', LogoutView.as_view(), name='logout'),
    path('accounts/resend-verification-email/', views.resend_verification_email, name='resend_verification_email'),
    path('accounts/password/reset/', PasswordResetView.as_view(), name='account_reset_password'),
    path('account-inactive/<str:email>/', views.account_inactive , name='account_inactive'),
    path('profile/', views.view_profile, name='view_profile'),
    path('profile/edit', views.update_profile, name='update_profile'),
    path('contact-us/', views.contact, name='contact'),
    path('feedback/', views.feedback, name='feedback'),
    path('activate/<str:uidb64>/<str:token>/', views.verify_email, name='verify_email'),
    path('get_question/', views.get_question, name="get_question"),
    path('create-interview-session/', views.create_interview_session, name='create_interview_session'),
    path('start-interview/', views.start_interview, name='start_interview'),
    path('save-answer/', views.save_answer, name='save_answer'),
    path('end-interview/', views.end_interview, name='end_interview'),
    path('display-interview-result/', views.display_result, name='display_result'),
    path('get-answer-automatically/', views.get_answer_automatically, name='get_answer_automatically'),
    path('check-review-status/', views.check_review_status, name="check_review_status"),
    path('speak_text/', views.speak_text, name="speak_text"),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]
