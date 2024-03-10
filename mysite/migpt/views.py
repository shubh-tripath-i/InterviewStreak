from django.http import JsonResponse
from migpt import utils
from django.shortcuts import render, redirect
from .forms import SignUpForm, UserProfileForm, UserInterviewForm, ContactUsForm, FeedbackForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from migpt import models
from migpt.helpers.tokens import account_activation_token
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse
from decimal import Decimal
from django import forms
from datetime import timedelta
import boto3
import base64
from django.conf import settings


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            mail_subject = 'Please Verify Your Email Address for InterviewStreak'
            message = render_to_string('migpt/message/account_verification_mail.html', {
                'user': user,
                'host': settings.HOST,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                        mail_subject, message, to=[to_email]
            )
            email.send()
            return render(request, 'migpt/message/email_verification.html', {})
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
        models.UserProfile.objects.create(user=user)
        return render(request, 'migpt/message/email_verification_succesful.html', {})
    else:
        return render(request, 'migpt/message/invalid_activation_link.html', {})


def speak_text(request):
    text = request.GET.get('text')
    polly = boto3.client('polly', region_name=settings.AWS_REGION)

    try:
        response = polly.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId='Matthew',
            Engine='neural',
            SampleRate='24000'
        )

        audio_data = response['AudioStream'].read()
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        return JsonResponse({'audio_data': audio_base64})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def index(request):
    context = {
    }
    return render(request, 'migpt/index.html', context)


def contact(request):
    if request.method == 'POST':
        form = ContactUsForm(request.POST)
        if form.is_valid():
            form.save()
            context = {"complete": True}
        else:
            context = {"form": form,
                       "complete": False}
    else:
        form = ContactUsForm()
        if request.user.is_authenticated:
            form.fields['email'].initial = request.user.email
            form.fields['name'].initial = request.user.first_name + " " + request.user.last_name
        context = {"form": form,
                   "complete": False}
    return render(request, 'migpt/contact.html', context)


def feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            context = {"complete": True}
        else:
            context = {"form": form,
                       "complete": False}
    else:
        form = FeedbackForm()
        if request.user.is_authenticated:
            form.fields['email'].initial = request.user.email
        context = {"form": form,
                   "complete": False}
    return render(request, 'migpt/feedback.html', context)


@login_required
def view_profile(request):
    user = User.objects.get(id=request.user.id)
    interviews = models.UserInterview.objects.filter(user=user, is_complete=True).order_by('-created_at')
    userprofile = models.UserProfile.objects.get(user=request.user)
    context = {"user": user,
               "interviews": interviews,
               "userprofile": userprofile
               }
    return render(request, 'migpt/view_profile.html', context)


@login_required
def update_profile(request):
    userprofile = models.UserProfile.objects.get(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=userprofile)
        if form.is_valid():
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
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors})
    else:
        form = UserInterviewForm()
        user = request.user
        if user.is_staff is False:
            form.fields['auto_answer'].widget = forms.HiddenInput()
        context = {
            'form': form,
            'interview': None
        }
        interview = models.UserInterview.objects.filter(user=request.user).last()
        if interview and interview.is_complete is False and interview.error_present is False:
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
            if interview.duration == timedelta(minutes=30):
                number_of_questions = 15
            elif interview.duration == timedelta(minutes=60):
                number_of_questions = 20
            elif interview.duration == timedelta(minutes=90):
                number_of_questions = 25
            elif interview.duration == timedelta(minutes=120):
                number_of_questions = 30
            else:
                raise Exception("Invalid duration")
            try:
                questions = utils.generate_questions(interview, number_of_questions)
            except Exception as e:
                interview.error_present = True
                interview.error_message = e
                interview.save()
                return render(request, 'migpt/message/interview_schedule_error.html', {})
            pos = 1
            for question in questions:
                # print(question)
                models.UserQuestionAnswer.objects.create(question=question, user=interview.user,
                                                        session=interview, pos=pos)
                pos += 1
        context = {'user_initial': interview.user.first_name[0]}
        return render(request, 'migpt/interview_interface.html', context)
    else:
        url = reverse('migpt:display_result') + f'?interview={interview.id}'
        return redirect(url)


def check_review_status(request):
    interview_id = request.GET.get('interview_id')
    interview = models.UserInterview.objects.get(id=interview_id)
    return JsonResponse({'review_generated': interview.review_generated})


@login_required
def end_interview(request):
    interview_id = request.GET.get('incomplete_interview_id')  # For displaying interview result
    if not interview_id:
        interview_id = request.session.get('interview_id')
    utils.complete_interview(interview_id)
    url = reverse('migpt:display_result') + f'?interview={interview_id}'
    return redirect(url)


@login_required
def display_result(request):
    interview_id = request.GET.get('interview')
    interview = models.UserInterview.objects.get(id=interview_id)
    if request.user != interview.user:
        return render(request, 'migpt/message/invalid_interview.html', {})
    questions = models.UserQuestionAnswer.objects.filter(user=interview.user,
                                                        session=interview, is_asked=True).order_by('pos')
    context = {
        'interview': interview,
        'questions': questions,
        'num_questions': len(questions)
    }
    return render(request, 'migpt/interview_result.html', context)


def get_question(request):
    interview_id = request.session.get('interview_id')
    interview = models.UserInterview.objects.get(id=interview_id)
    question = models.UserQuestionAnswer.objects.filter(user=interview.user,
                                                        session=interview,
                                                        is_asked=False).order_by('pos').first()
    if not question:
        # utils.complete_interview(interview_id)
        data = {
            'success': True,
            'redirect': '/end-interview'
        }
        return JsonResponse(data)
    request.session['question_id'] = question.id
    data = {
        'success': True,
        'question': question.question,
        'auto_answer': interview.auto_answer
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
            if question.answer is None:
                question.answer = answer_text
                question.is_asked = True
                question.save()
                if interview.cross_question:

                    if interview.duration == timedelta(minutes=30):
                        number_of_cross_questions = 1
                        depth_cross_questioning = 2
                        importance_score = 8
                    elif interview.duration == timedelta(minutes=60):
                        number_of_cross_questions = 2
                        depth_cross_questioning = 2
                        importance_score = 9
                    elif interview.duration == timedelta(minutes=90):
                        number_of_cross_questions = 2
                        depth_cross_questioning = 2
                        importance_score = 8
                    elif interview.duration == timedelta(minutes=120):
                        number_of_cross_questions = 2
                        depth_cross_questioning = 3
                        importance_score = 7
                    else:
                        raise Exception("Invalid duration")

                    decimal_part = str(question.pos).split('.')[1]
                    if float(decimal_part) == 0:
                        pos_to_add = '0.1'
                    else:
                        depth = len(decimal_part)
                        pos_to_add = '0.'
                        for i in range(depth):
                            pos_to_add += '0'
                        pos_to_add += '1'
                    pos = Decimal(str(question.pos)) + Decimal(pos_to_add)
                    depth = len(str(pos).split('.')[1])
                    pos_to_add = Decimal(pos_to_add)
                    if depth <= depth_cross_questioning:
                        cross_questions = utils.generate_cross_question(interview, question,
                                                                        number_of_cross_questions,
                                                                        importance_score)
                        print("Cross questions generated")
                        if len(cross_questions) > number_of_cross_questions:
                            pos_to_add = pos_to_add*Decimal('0.1')
                            pos = Decimal(str(question.pos)) + Decimal(pos_to_add)
                        for cross_question in cross_questions:
                            print(cross_question)
                            models.UserQuestionAnswer.objects.create(question=cross_question, user=interview.user,
                                                                    session=interview, pos=pos)
                            pos += pos_to_add
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Answer is missing'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_answer_automatically(request):
    if request.user.is_staff is False:
        return JsonResponse({'success': False, 'error': 'Invalid request'})
    if request.method == 'GET':
        interview_id = request.session.get('interview_id')
        interview = models.UserInterview.objects.get(id=interview_id)
        question = models.UserQuestionAnswer.objects.get(id=request.session.get('question_id'))
        answer_text = utils.generate_answer(interview.job_role, question.question)
        return JsonResponse({'success': True, 'answer': answer_text})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
