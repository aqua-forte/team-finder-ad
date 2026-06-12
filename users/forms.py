import re
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from .models import User, Skill


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


class LoginForm(AuthenticationForm):
    pass


class ProfileForm(forms.ModelForm):
    skills_text = forms.CharField(
        label="Навыки",
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Навыки через запятую",
                "class": "form-control",
            }
        ),
    )

    class Meta:
        model = User
        fields = (
            "avatar",
            "name",
            "surname",
            "email",
            "about",
            "phone",
            "github_url",
        )
        widgets = {
            "avatar": forms.FileInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "surname": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "about": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "github_url": forms.TextInput(attrs={"class": "form-control"}),
        }

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

    def save(self, commit=True):
        user = super().save(commit=False)
        skills_text = self.cleaned_data.get("skills_text")
        if skills_text:
            skills = [s.strip() for s in skills_text.split(",") if s.strip()]
            skill_objs = []

            for name in skills:
                skill_obj, _ = Skill.objects.get_or_create(name=name)
                skill_objs.append(skill_obj)
            if commit:
                user.save()
                user.skills.set(skill_objs)
        elif commit:
            user.save()
        return user
