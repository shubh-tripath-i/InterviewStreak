from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from datetime import timedelta


class UserProfile(models.Model):

    choices_for_sex = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('not_disclosed', 'Rather not disclose'))

    user = models.OneToOneField(
        User, related_name='userprofile', on_delete=models.CASCADE)
    token = models.IntegerField(default=0)
    intro = models.CharField(max_length=200, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    sex = models.CharField(max_length=15, null=True,
                           blank=True, choices=choices_for_sex)
    dob = models.DateTimeField(null=True, blank=True)
    current_job_role = models.CharField(max_length=100, null=True, blank=True)
    current_company = models.CharField(max_length=100, null=True, blank=True)
    highest_degree = models.CharField(max_length=100, null=True, blank=True)
    linkedin_profile_url = models.URLField(null=True, blank=True)
    github_profile_url = models.URLField(null=True, blank=True)
    last_seen = models.DateTimeField(blank=True, null=True)
    percent_profile_completed = models.IntegerField(default=0)
    # profile_picture = models.ImageField(
    #     blank=True, null=True,)  #upload_to=settings.PROFILE_PICTURE_UPLOAD_PATH, validators=[custom_validators.validate_image_extension])
    # resume = models.FileField(
    #     blank=True, null=True,
    #     upload_to='resumes',)
    #     #validators=[custom_validators.validate_pdf_extension, custom_validators.validate_file_size])
    device = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=100, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    region = models.CharField(max_length=100, blank=True, default='')
    postal_code = models.CharField(max_length=15, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class UserJobSearch(models.Model):
    choices_for_work_preference = (
        ('onsite', 'Onsite'),
        ('remote', 'Remote'),
        ('any', 'Onsite or Remote')
    )

    user = models.OneToOneField(
        User, related_name='userjobsearch', on_delete=models.CASCADE)
    bio = models.CharField(max_length=400, null=True, blank=True)
    looking_for_job = models.BooleanField(default=False)
    share_profile_with_recruiter = models.BooleanField(default=False)
    looking_for_freelancing = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    work_preference = models.CharField(max_length=6, null=True,
                                       blank=True, choices=choices_for_work_preference)
    expected_salary = models.PositiveIntegerField(default=0)
    out_of_country = models.BooleanField(default=False)


class UserInterview(models.Model):
    choices_for_difficulty = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    )

    choices_for_question_type = (
        ('all', 'All'),
        ('coding', 'Coding'),
        ('theory', 'Theory'),
        ('behavioural', 'Behavioural'),
        ('puzzle', 'Puzzle'),
        ('design', 'Design')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    review = models.TextField(max_length=1024)
    strong_points = models.TextField(max_length=1024, null=True, blank=True)
    weak_points = models.TextField(max_length=1024, null=True, blank=True)
    improvements = models.TextField(max_length=1024, null=True, blank=True)
    is_selected = models.BooleanField(null=True)
    company = models.CharField(max_length=50, null=True, blank=True)
    job_role = models.CharField(max_length=50)
    interview_round = models.PositiveIntegerField(default=1,
                                                  validators=[MinValueValidator(1),
                                                              MaxValueValidator(10)],
                                                  null=True, blank=True)
    job_description = models.CharField(max_length=400, null=True, blank=True)
    subject = models.CharField(max_length=100, null=True, blank=True,
                               help_text="Put a comma after each subject")
    topic = models.CharField(max_length=100, null=True, blank=True,
                             help_text="Put a comma after each topic")
    tools = models.CharField(max_length=500, null=True, blank=True,
                             help_text="Put a comma after each tool")
    difficulty_level = models.CharField(max_length=6, null=True,
                                        blank=True, choices=choices_for_difficulty)
    question_type = models.CharField(max_length=12, null=True, default="all",
                                     blank=True, choices=choices_for_question_type)
    user_instructions = models.TextField(null=True, blank=True,)  # To get custom user instructions
    tags = models.CharField(max_length=500, null=True, blank=True,
                            help_text="Put a comma after each tag")
    duration = models.DurationField(default=timedelta(minutes=30), null=True, blank=True)
    is_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # recording =


class UserQuestionAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(UserInterview, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField(null=True, blank=True)
    perfect_answer = models.TextField(null=True, blank=True)
    score = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    is_asked = models.BooleanField(default=False)
    review = models.TextField(null=True, blank=True)
    improvements = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
