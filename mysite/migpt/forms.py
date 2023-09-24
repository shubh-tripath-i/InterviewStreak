from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from migpt import models
from django.utils.text import slugify
import random

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2', )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            self.cleaned_data['email'] = ''
            raise forms.ValidationError("This email is already in use.")
        return email

    def save(self, commit=True):
        user = super(SignUpForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        username = slugify(user.email.split('@')[0])
        i = 0
        while User.objects.filter(username=username).exists():
            username = f"{slugify(user.email.split('@')[0])}{i}"
            i += 1

        user.username = username
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = models.UserProfile
        fields = ('intro', 'location', 'sex', 'dob', 'current_job_role', 'current_company',
                  'highest_degree', 'linkedin_profile_url', 'github_profile_url'
                  )


class UserInterviewForm(forms.ModelForm):
    class Meta:
        model = models.UserInterview
        fields = ('job_role',)
        # fields = ('company', 'job_role', 'interview_round', 'job_description', 'subject', 'topic',
        #           'tools', 'difficulty_level', 'question_type', #'user_instructions',
        #           'tags', 'duration')