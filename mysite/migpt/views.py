from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from migpt import utils
from django.shortcuts import render, redirect
from .forms import SignUpForm, UserProfileForm, UserInterviewForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from migpt import models
from migpt.helpers.tokens import account_activation_token
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth import get_user_model
from django.urls import reverse
import ast


class CustomPasswordResetView(PasswordResetView):
    def form_valid(self, form):
        email = form.cleaned_data['email']
        User = get_user_model()

        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            # Email doesn't exist in the database; show an error message
            return HttpResponse('Email does not exist')

        return super().form_valid(form)


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
            # email.send()
            return HttpResponse('Please confirm your email address to complete the registration')
    else:
        form = SignUpForm()
    return render(request, 'migpt/signup.html',{'form': form})


def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        models.UserProfile.objects.create(user=user)
        return HttpResponse('Email verification succesful')
    else:
        return HttpResponse('Activation link is invalid!')


def index(request):
    context = {
    }
    return render(request, 'migpt/index.html', context)


@login_required
def view_profile(request):
    user = User.objects.get(id=request.user.id)
    interviews = models.UserInterview.objects.filter(user=user).order_by('-created_at')
    context = {"name": user.first_name + user.last_name,
               "interviews": interviews
               }
    return render(request, 'migpt/view_profile.html', context)


@login_required
def update_profile(request):
    userprofile = models.UserProfile.objects.get(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=userprofile)
        if form.is_valid():
            print("is valid called")
            form.save()
            return redirect("migpt:update_profile")
    else:
        form = UserProfileForm(instance=userprofile)
    return render(request, 'migpt/edit_profile.html', {'form': form})


@login_required
def create_interview_session(request):
    # TODO: Fix number of tokens required on basis of time duration and other factors
    # Decide when to reduce that tokens in userprofile
    if request.method == 'POST':
        form = UserInterviewForm(request.POST)
        if form.is_valid():
            interview = form.save(commit=False)
            interview.user = request.user
            interview.is_complete = False
            interview = form.save()
            request.session['interview_id'] = interview.id
            return redirect("migpt:start_interview")
    else:
        form = UserInterviewForm()
        context = {
            'form': form,
            'interview': None
        }
        interview = models.UserInterview.objects.filter(user=request.user).last()
        if interview.is_complete is False:
            context['interview'] = interview
            request.session['interview_id'] = interview.id
    return render(request, 'migpt/create_interview_session.html', context)


@login_required
def start_interview(request):
    interview = models.UserInterview.objects.get(id=request.session.get('interview_id'))
    if not interview.is_complete:
        # Check if questions are already there
        questions = models.UserQuestionAnswer.objects.filter(user=interview.user,
                                                             session=interview)
        if not questions:
            questions = utils.generate_questions(interview)
            print(len(questions), "questions generated")
            for question in questions:
                print(question, type(question))
                models.UserQuestionAnswer.objects.create(question=question, user=interview.user,
                                                        session=interview)
        context = {}
        return render(request, 'migpt/interview_interface.html', context)
    else:
        return HttpResponse("Interview Over")


@login_required
def end_interview(request):
    interview_id = request.session.get('interview_id')
    utils.complete_interview(interview_id)
    url = reverse('migpt:display_result') + f'?interview={interview_id}'
    print(url)
    return redirect(url)


def display_result(request):
    interview_id = request.GET.get('interview')
    interview = models.UserInterview.objects.get(id=interview_id)
    if request.user != interview.user:
        return HttpResponse("Invalid Request")
    questions = models.UserQuestionAnswer.objects.filter(user=interview.user,
                                                        session=interview, is_asked=True)
    context = {
        'interview': interview,
        'questions': questions
    }
    return render(request, 'migpt/interview_result.html', context)


def get_question(request):
    interview_id = request.session.get('interview_id')
    interview = models.UserInterview.objects.get(id=interview_id)
    question = models.UserQuestionAnswer.objects.filter(user=interview.user,
                                                        session=interview, is_asked=False).first()
    if not question:
        utils.complete_interview(interview_id)
        data = {
            'success': True,
        }
        return JsonResponse(data)
    request.session['question_id'] = question.id
    data = {
        'success': True,
        'question': question.question
    }
    return JsonResponse(data)


def save_answer(request):
    if request.method == 'POST':
        answer_text = request.POST.get('answer')
        interview_id = request.session.get('interview_id')
        interview = models.UserInterview.objects.get(id=interview_id)
        if interview.is_complete:
            return JsonResponse({'success': False, 'error': 'Interview Already Complete'})
        if answer_text:
            question = models.UserQuestionAnswer.objects.get(id=request.session.get('question_id'))
            question.answer = answer_text
            question.is_asked = True
            question.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Answer is missing'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
