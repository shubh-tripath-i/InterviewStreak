from django.http import JsonResponse
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
from django.http import HttpResponse


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


def index(request):
    context = {
    }
    return render(request, 'migpt/index.html', context)


@login_required
def view_profile(request):
    user = User.objects.get(id=request.user.id)
    context = {"name": user.first_name + user.last_name
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
    return render(request, 'migpt/create_interview_session.html', {'form': form})


@login_required
def start_interview(request):
    interview = models.UserInterview.objects.get(id=request.session.get('interview_id'))
    questions = utils.generate_questions(interview)
    for question in questions:
        models.UserQuestionAnswer.objects.create(question=question, user=interview.user,
                                                 session=interview)
    context = {'question': questions[0]}
    return render(request, 'migpt/interview_interface.html', context)


def get_question(request):
    interview = models.UserInterview.objects.get(id=request.session.get('interview_id'))
    question = models.UserQuestionAnswer.objects.filter(user=interview.user,
                                                        session=interview, is_asked=False).first()
    if not question:
        # Redirect to success page or something
        interview = models.UserInterview.objects.get(id=request.session.get('interview_id'))
        interview.is_complete = True
        # Fill score and review
        interview.save()
        return redirect("migpt:index")
    request.session['question_id'] = question.id
    data = {
        'success': True,
        'question': question.question
    }
    return JsonResponse(data)


def save_answer(request):
    if request.method == 'POST':
        answer_text = request.POST.get('answer')
        interview = models.UserInterview.objects.get(id=request.session.get('interview_id'))
        if interview.is_complete:
            return JsonResponse({'success': False, 'error': 'Interview Already Complete'})
        if answer_text:
            question = models.UserQuestionAnswer.objects.get(id=request.session.get('question_id'))
            question.answer = answer_text
            question.is_asked = True
            # Generate review and score
            question.save()
            interview = models.UserInterview.objects.get(id=request.session.get('interview_id'))
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Answer is missing'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
