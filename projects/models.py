from django.conf import settings
from django.db import models

from .constants import (PROJECT_GITHUB_URL_MAX_LENGTH, PROJECT_NAME_MAX_LENGTH,
                        PROJECT_STATUS_MAX_LENGTH)


class Project(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    name = models.CharField(
        max_length=PROJECT_NAME_MAX_LENGTH,
        verbose_name="Название проекта",
    )
    description = models.TextField(blank=True, verbose_name="Описание")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        verbose_name="Владелец",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    status = models.CharField(
        max_length=PROJECT_STATUS_MAX_LENGTH,
        choices=Status.choices,
        default=Status.OPEN,
        verbose_name="Статус",
    )
    github_url = models.URLField(
        max_length=PROJECT_GITHUB_URL_MAX_LENGTH,
        blank=True,
        default="",
        verbose_name="GitHub URL",
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="participated_projects",
        blank=True,
        verbose_name="Участники",
    )
    favorites = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="favorite_projects",
        blank=True,
        verbose_name="Избранное",
    )

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
