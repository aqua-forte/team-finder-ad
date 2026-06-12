from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import (
    SKILL_NAME_MAX_LENGTH,
    USER_NAME_MAX_LENGTH,
    USER_SURNAME_MAX_LENGTH,
    USER_ABOUT_MAX_LENGTH,
    USER_PHONE_MAX_LENGTH,
    USER_GITHUB_URL_MAX_LENGTH,
)
from .validators import validate_github_url
from .services import generate_user_avatar


class Skill(models.Model):
    name = models.CharField(
        max_length=SKILL_NAME_MAX_LENGTH, unique=True, verbose_name="Название навыка"
    )

    class Meta:
        verbose_name = "Навык"
        verbose_name_plural = "Навыки"
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractUser):
    name = models.CharField(max_length=USER_NAME_MAX_LENGTH, verbose_name="Имя")
    surname = models.CharField(
        max_length=USER_SURNAME_MAX_LENGTH, verbose_name="Фамилия"
    )
    email = models.EmailField(unique=True, verbose_name="Email")
    avatar = models.ImageField(
        upload_to="avatars/", blank=True, default="", verbose_name="Аватар"
    )
    about = models.TextField(
        max_length=USER_ABOUT_MAX_LENGTH, blank=True, verbose_name="О себе"
    )
    phone = models.CharField(
        max_length=USER_PHONE_MAX_LENGTH, default="", verbose_name="Телефон"
    )
    github_url = models.CharField(
        max_length=USER_GITHUB_URL_MAX_LENGTH,
        blank=True,
        verbose_name="GitHub",
        validators=[validate_github_url],
    )
    skills = models.ManyToManyField(Skill, blank=True, verbose_name="Навыки")

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["-date_joined"]

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "name", "surname"]

    def save(self, *args, **kwargs):
        if not self.avatar:
            filename, content = generate_user_avatar(self)
            self.avatar.save(filename, content, save=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} {self.surname}"
