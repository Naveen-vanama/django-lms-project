from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (
        ('Role & Profile', {
            'fields': (
                'role',
                'phone',
                'profile_picture',
                'bio',
                'date_of_birth',
                'is_approved',
            )
        }),
    )

    list_display = (
        'username',
        'email',
        'role',
        'is_active',
        'is_approved',
    )

    list_filter = ('role', 'is_active', 'is_approved')

    # ✅ ADD THIS ACTION
    actions = ['approve_users']

    def approve_users(self, request, queryset):
        queryset.update(is_approved=True, is_active=True)

    approve_users.short_description = "Approve selected users"