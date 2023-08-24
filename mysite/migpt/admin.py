from django.contrib import admin
from migpt import models

# Register your models here.

class UserProfileAdmin(admin.ModelAdmin):
    raw_id_fields = ('user',)
    list_display = ('user', 'intro', 'location', 'sex', 'dob', 'current_job_role', 'current_company',
                    'highest_degree', 'linkedin_profile_url', 'github_profile_url', 'last_seen',
                    'percent_profile_completed', 'device', 'country')
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']


admin.site.register(models.UserProfile, UserProfileAdmin)
