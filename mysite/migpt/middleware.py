from django.contrib.auth import get_user_model
from django.contrib.auth import login
import migpt.models as models

class AutoLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        User = get_user_model()
        if not request.user.is_authenticated:
            user, created = User.objects.get_or_create(
                email="demo@example.com",
                defaults={
                    "username": "demo_user",
                    "first_name": "Demo",
                    "last_name": "User",
                    "is_active": True,
                    "is_staff": True,
                    "is_superuser": True,
                },
            )
            user.backend = "django.contrib.auth.backends.ModelBackend"
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            models.UserProfile.objects.create(user=user)
        response = self.get_response(request)
        return response
