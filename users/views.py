import json
from http import HTTPStatus

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from team_finder.utils import paginate_queryset
from projects.models import Project

from .models import Skill, User
from .forms import UserRegistrationForm, ProfileForm, LoginForm
from .constants import (
    PAGINATION_LIMIT,
    FILTER_FAVORITES_AUTHORS,
    FILTER_MY_PROJECTS_AUTHORS,
    FILTER_MY_PROJECT_FANS,
    FILTER_MY_PROJECTS_PARTICIPANTS,
    SKILLS_SUGGESTIONS_LIMIT,
)


def register(request):
    if request.method != "POST":
        form = UserRegistrationForm()
        return render(request, "users/register.html", {"form": form})

    form = UserRegistrationForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, "users/register.html", {"form": form})

    form.save()
    return redirect("users:login")


def login_view(request):
    if request.method != "POST":
        form = LoginForm()
        return render(request, "users/login.html", {"form": form})

    form = LoginForm(data=request.POST)
    if not form.is_valid():
        return render(request, "users/login.html", {"form": form})

    user = form.get_user()
    login(request, user)
    return redirect("projects:project_list")


def logout_view(request):
    logout(request)
    return redirect("projects:project_list")


def profile(request, pk):
    user = get_object_or_404(User, pk=pk)
    return render(request, "users/user-details.html", {"user": user})


def edit_profile(request):
    if not request.user.is_authenticated:
        return redirect("users:login")

    if request.method != "POST":
        form = ProfileForm(instance=request.user)
        return render(
            request, "users/edit_profile.html", {"form": form, "user": request.user}
        )

    form = ProfileForm(
        request.POST or None, request.FILES or None, instance=request.user
    )
    if not form.is_valid():
        return render(
            request, "users/edit_profile.html", {"form": form, "user": request.user}
        )

    form.save()
    messages.success(request, "Profile updated!")
    return redirect("users:profile", pk=request.user.pk)


def change_password(request):
    if not request.user.is_authenticated:
        return redirect("users:login")

    if request.method != "POST":
        form = PasswordChangeForm(request.user)
        return render(
            request, "users/change_password.html", {"form": form, "user": request.user}
        )

    form = PasswordChangeForm(request.user, request.POST or None)
    if not form.is_valid():
        return render(
            request, "users/change_password.html", {"form": form, "user": request.user}
        )

    user = form.save()
    messages.success(request, "Password changed!")
    return redirect("users:profile", pk=user.pk)


@login_required
def admin_change_password(request, pk):
    if not request.user.is_staff:
        return redirect("users:profile", pk=pk)

    target_user = get_object_or_404(User, pk=pk)
    if request.method != "POST":
        return render(
            request, "users/admin_change_password.html", {"user": target_user}
        )

    new_password = request.POST.get("password")
    if not new_password:
        messages.error(request, "Please provide a new password.")
        return render(
            request, "users/admin_change_password.html", {"user": target_user}
        )

    target_user.set_password(new_password)
    target_user.save()
    messages.success(request, f"Password for {target_user} changed successfully!")
    return redirect("users:profile", pk=pk)


@login_required
def admin_toggle_user_status(request, pk):
    if not request.user.is_staff:
        return redirect("users:profile", pk=pk)

    target_user = get_object_or_404(User, pk=pk)
    target_user.is_active = not target_user.is_active
    target_user.save()
    status = "blocked" if not target_user.is_active else "unblocked"
    messages.success(request, f"User {target_user} has been {status}.")
    return redirect("users:profile", pk=pk)


@login_required
def admin_delete_user(request, pk):
    if not request.user.is_staff:
        return redirect("users:profile", pk=pk)

    target_user = get_object_or_404(User, pk=pk)
    target_user.delete()
    messages.success(request, "User deleted successfully.")
    return redirect("users:user_list")


def user_list(request):
    skill_name = request.GET.get("skill")
    filter_type = request.GET.get("filter")
    users = User.objects.prefetch_related("skills").order_by("-date_joined")

    if skill_name:
        users = users.filter(skills__name__iexact=skill_name)

    if request.user.is_authenticated and filter_type:
        if filter_type == FILTER_FAVORITES_AUTHORS:
            fav_projects = Project.objects.filter(
                favorites=request.user
            ).select_related("owner")
            users = users.filter(owned_projects__in=fav_projects).distinct()
        elif filter_type == FILTER_MY_PROJECTS_AUTHORS:
            my_projects = Project.objects.filter(
                participants=request.user
            ).select_related("owner")
            users = users.filter(owned_projects__in=my_projects).distinct()
        elif filter_type == FILTER_MY_PROJECT_FANS:
            my_owned_projects = Project.objects.filter(owner=request.user)
            users = users.filter(favorite_projects__in=my_owned_projects).distinct()
        elif filter_type == FILTER_MY_PROJECTS_PARTICIPANTS:
            my_projects = Project.objects.filter(participants=request.user)
            users = (
                users.filter(participated_projects__in=my_projects)
                .exclude(pk=request.user.pk)
                .distinct()
            )

    page_number = request.GET.get("page", 1)
    page_obj = paginate_queryset(users, page_number, PAGINATION_LIMIT)

    return render(
        request,
        "users/participants.html",
        {
            "all_skills": Skill.objects.all(),
            "active_skill": skill_name,
            "active_filter": filter_type,
            "page_obj": page_obj,
        },
    )


@login_required
def add_skill(request, user_id):
    if request.user.pk != user_id:
        return JsonResponse(
            {"error": "You can only edit your own skills"}, status=HTTPStatus.FORBIDDEN
        )

    if request.method == "POST":
        data = json.loads(request.body)
        skill_id = data.get("skill_id")
        skill_name = data.get("name")

        created = False
        if skill_id:
            skill = get_object_or_404(Skill, pk=skill_id)
        elif skill_name:
            skill, created = Skill.objects.get_or_create(name=skill_name)
        else:
            return JsonResponse(
                {"error": "Skill ID or name is required"}, status=HTTPStatus.BAD_REQUEST
            )

        added = not request.user.skills.filter(pk=skill.pk).exists()
        request.user.skills.add(skill)

        return JsonResponse(
            {
                "skill_id": skill.id,
                "name": skill.name,
                "created": created,
                "added": added,
            }
        )
    return JsonResponse(
        {"error": "Invalid method"}, status=HTTPStatus.METHOD_NOT_ALLOWED
    )


@login_required
def remove_skill(request, user_id, skill_id):
    if request.user.pk != user_id:
        return JsonResponse(
            {"error": "You can only edit your own skills"}, status=HTTPStatus.FORBIDDEN
        )

    if request.method == "POST":
        skill = get_object_or_404(Skill, pk=skill_id)
        if skill in request.user.skills.all():
            request.user.skills.remove(skill)
            return JsonResponse({"status": "ok"})
        return JsonResponse(
            {"error": "User does not have this skill"}, status=HTTPStatus.BAD_REQUEST
        )
    return JsonResponse(
        {"error": "Invalid method"}, status=HTTPStatus.METHOD_NOT_ALLOWED
    )


def get_skills_suggestions(request):
    query = request.GET.get("q", "")
    skills = Skill.objects.filter(name__icontains=query)[:SKILLS_SUGGESTIONS_LIMIT]
    return JsonResponse(
        [{"id": skill.id, "name": skill.name} for skill in skills], safe=False
    )
