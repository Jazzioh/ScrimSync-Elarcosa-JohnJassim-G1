from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "in_game_name", "is_staff")
    list_filter = ("role", "is_staff", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        (
            "ScrimSync Profile",
            {"fields": ("role", "in_game_name", "discord_tag", "contact_number", "avatar")},
        ),
    )