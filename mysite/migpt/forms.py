from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from migpt import models


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            self.cleaned_data['email'] = ''
            raise forms.ValidationError("This email is already in use.")
        return email

    def save(self, commit=True):
        user = super(SignUpForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = models.UserProfile
        fields = ('intro', 'location', 'sex', 'dob', 'current_job_role', 'current_company',
                  'highest_degree', 'linkedin_profile_url', 'github_profile_url'
                  )