import json
import re
import urllib.request
from django import forms
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import User, Skill
from projects.models import Project


class UserRegistrationForm(forms.ModelForm):
    name = forms.CharField(label="Имя", max_length=150)
    surname = forms.CharField(label="Фамилия", max_length=150)
    email = forms.EmailField(label="Email", required=True)
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("name", "surname", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data.get("email")
        user.set_password(self.cleaned_data.get("password"))
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    avatar = forms.CharField(
        label="Ссылка на аватар",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    skills_text = forms.CharField(
        label="Навыки",
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Навыки через запятую", "class": "form-control"}
        ),
    )

    class Meta:
        model = User
        fields = ("name", "surname", "email", "about", "phone", "github_url")
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "email": "Email",
            "about": "О себе",
            "phone": "Телефон",
            "github_url": "GitHub",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "surname": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "about": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "github_url": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url")
        if url:
            if "github.com" not in url:
                raise forms.ValidationError("Ссылка должна вести на github.com")
        return url

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if not phone:
            return phone

        if not (re.fullmatch(r"8\d{10}", phone) or re.fullmatch(r"\+7\d{10}", phone)):
            raise forms.ValidationError(
                "Номер телефона должен быть в формате " "8XXXXXXXXXX или +7XXXXXXXXXX"
            )

        alt_phone = (
            phone.replace("+7", "8")
            if phone.startswith("+7")
            else "+" + phone.replace("8", "7", 1)
        )
        if (
            User.objects.filter(Q(phone=phone) | Q(phone=alt_phone))
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError(
                "Этот номер телефона уже используется другим пользователем"
            )

        return phone

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Pre-fill skills_text with existing skills joined by comma
            skills = self.instance.skills.all()
            self.initial["skills_text"] = ", ".join([s.name for s in skills])

    def save(self, commit=True):
        user = self.instance

        # Explicitly assign all model fields from cleaned_data
        user.name = self.cleaned_data.get("name", user.name)
        user.surname = self.cleaned_data.get("surname", user.surname)
        user.email = self.cleaned_data.get("email", user.email)
        user.about = self.cleaned_data.get("about", user.about)
        user.phone = self.cleaned_data.get("phone", user.phone)
        user.github_url = self.cleaned_data.get("github_url", user.github_url)

        # Handle avatar as URL
        avatar_value = self.cleaned_data.get("avatar")
        if (
            avatar_value
            and isinstance(avatar_value, str)
            and avatar_value.startswith(("http://", "https://"))
        ):
            try:
                # Download image
                with urllib.request.urlopen(avatar_value, timeout=5) as response:
                    image_data = response.read()
                    # Save to ImageField
                    filename = f"avatar_{user.pk or 'temp'}.jpg"
                    user.avatar.save(filename, ContentFile(image_data), save=False)
            except Exception:
                # If download fails, we keep the existing avatar
                pass

        if commit:
            user.save()
            # Handle skills update
            skills_str = self.cleaned_data.get("skills_text", "")
            if skills_str:
                skill_names = [
                    name.strip() for name in skills_str.split(",") if name.strip()
                ]
                skill_objects = []
                for name in skill_names:
                    skill, _ = Skill.objects.get_or_create(name=name)
                    skill_objects.append(skill)
                user.skills.set(skill_objects)
            else:
                user.skills.clear()
        return user


def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("users:login")
    else:
        form = UserRegistrationForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        from django.contrib.auth.forms import AuthenticationForm

        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("projects:project_list")
    else:
        from django.contrib.auth.forms import AuthenticationForm

        form = AuthenticationForm()
        form.fields["username"].label = "Email"
        form.fields["password"].label = "Пароль"
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("projects:project_list")


def profile(request, pk):
    user = get_object_or_404(User, pk=pk)
    return render(request, "users/user-details.html", {"user": user})


def edit_profile(request):
    if not request.user.is_authenticated:
        return redirect("users:login")

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated!")
            return redirect("users:profile", pk=request.user.pk)
    else:
        form = ProfileForm(instance=request.user)
    return render(
        request, "users/edit_profile.html", {"form": form, "user": request.user}
    )


def change_password(request):
    if not request.user.is_authenticated:
        return redirect("users:login")

    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Password changed!")
            return redirect("users:profile", pk=user.pk)
    else:
        form = PasswordChangeForm(request.user)
    return render(
        request, "users/change_password.html", {"form": form, "user": request.user}
    )


@login_required
def admin_change_password(request, pk):
    if not request.user.is_staff:
        return redirect("users:profile", pk=pk)

    target_user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        new_password = request.POST.get("password")
        if new_password:
            target_user.set_password(new_password)
            target_user.save()
            messages.success(
                request, f"Password for {target_user} changed successfully!"
            )
            return redirect("users:profile", pk=pk)
        else:
            messages.error(request, "Please provide a new password.")

    return render(request, "users/admin_change_password.html", {"user": target_user})


@login_required
def admin_block_user(request, pk):
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
    users = User.objects.all().prefetch_related("skills").order_by("-date_joined")

    if skill_name:
        users = users.filter(skills__name__iexact=skill_name)

    if request.user.is_authenticated and filter_type:
        if filter_type == "favorites_authors":
            # Authors of projects that are in the current user's favorites
            fav_projects = Project.objects.filter(favorites=request.user)
            users = users.filter(owned_projects__in=fav_projects).distinct()
        elif filter_type == "my_projects_authors":
            # Authors of projects in which the current user participates
            my_projects = Project.objects.filter(participants=request.user)
            users = users.filter(owned_projects__in=my_projects).distinct()
        elif filter_type == "my_project_fans":
            # Users who added the current user's projects to their favorites
            my_owned_projects = Project.objects.filter(owner=request.user)
            users = users.filter(favorite_projects__in=my_owned_projects).distinct()
        elif filter_type == "my_projects_participants":
            # Other participants of projects in which the current user participates
            my_projects = Project.objects.filter(participants=request.user)
            users = (
                users.filter(participated_projects__in=my_projects)
                .exclude(pk=request.user.pk)
                .distinct()
            )

    paginator = Paginator(users, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "users/participants.html",
        {
            "all_skills": Skill.objects.all().order_by("name"),
            "active_skill": skill_name,
            "active_filter": filter_type,
            "page_obj": page_obj,
        },
    )


@login_required
def add_skill(request, user_id):
    if request.user.pk != user_id:
        return JsonResponse({"error": "You can only edit your own skills"}, status=403)

    if request.method == "POST":
        data = json.loads(request.body)
        skill_id = data.get("skill_id")
        skill_name = data.get("name")

        if skill_id:
            skill = get_object_or_404(Skill, pk=skill_id)
        elif skill_name:
            skill, created = Skill.objects.get_or_create(name=skill_name)
        else:
            return JsonResponse({"error": "Skill ID or name is required"}, status=400)

        request.user.skills.add(skill)
        return JsonResponse({"id": skill.id, "name": skill.name})
    return JsonResponse({"error": "Invalid method"}, status=405)


@login_required
def remove_skill(request, user_id, skill_id):
    if request.user.pk != user_id:
        return JsonResponse({"error": "You can only edit your own skills"}, status=403)

    if request.method == "POST":
        skill = get_object_or_404(Skill, pk=skill_id)
        if skill in request.user.skills.all():
            request.user.skills.remove(skill)
            return JsonResponse({"status": "ok"})
        return JsonResponse({"error": "User does not have this skill"}, status=400)
    return JsonResponse({"error": "Invalid method"}, status=405)


def get_skills_suggestions(request):
    query = request.GET.get("q", "")
    skills = Skill.objects.filter(name__icontains=query)[:10]
    return JsonResponse([{"id": s.id, "name": s.name} for s in skills], safe=False)
