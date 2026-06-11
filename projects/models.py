from django.db import models
from django.conf import settings


class Project(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("closed", "Closed"),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=6, choices=STATUS_CHOICES, default="open")
    github_url = models.URLField(max_length=500, blank=True, null=True)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="participated_projects",
        blank=True,
    )
    favorites = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="favorite_projects",
        blank=True,
    )

    def __str__(self):
        return self.name
