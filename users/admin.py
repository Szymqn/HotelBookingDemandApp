from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = [
        (
            None,
            {
                'fields': (
                    'username',
                    'password',
                    'is_superuser',
                    'is_premium',
                )
            },
        )
    ]


admin.site.register(CustomUser, CustomUserAdmin)
