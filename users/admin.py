from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Skill, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "name", "surname", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active")
    search_fields = ("email", "name", "surname")
    fieldsets = UserAdmin.fieldsets + (
        (
            "Additional Info",
            {
                "fields": ("avatar", "about", "phone", "github_url"),
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Additional Info",
            {
                "fields": ("avatar", "about", "phone", "github_url"),
            },
        ),
    )


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
