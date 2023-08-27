from django.http import JsonResponse
from migpt import utils
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import SignUpForm, UserProfileForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from migpt import models
from migpt.helpers.tokens import account_activation_token
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.http import HttpResponse

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
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activation link has been sent to your email id'
            message = render_to_string('migpt/account_verification_mail.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                        mail_subject, message, to=[to_email]
            )
            print(message)
            #email.send()
            return HttpResponse('Please confirm your email address to complete the registration')
    else:
        form = SignUpForm()
    return render(request, 'migpt/signup.html', {'form': form})


def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return HttpResponse('Email verification succesful')
    else:
        return HttpResponse('Activation link is invalid!')


def call_llm(request):
    chain = utils.make_chain()
    data = {
        'success': True,
        'message': "Hello there!"
    }
    return JsonResponse(data)
