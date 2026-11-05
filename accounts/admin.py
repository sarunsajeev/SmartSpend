from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class SmartSpendUserAdmin(UserAdmin):
    """Use Django's built-in user administration for the custom user model."""

    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff',
        'last_login', 'date_joined',
    )
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    date_hierarchy = 'date_joined'
    readonly_fields = ('last_login', 'date_joined')

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('username', 'email', 'password1', 'password2'),
            },
        ),
    )
