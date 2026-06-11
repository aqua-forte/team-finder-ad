from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont
import random
import io


class Skill(models.Model):
    name = models.CharField(max_length=124, unique=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    name = models.CharField(max_length=124, default="")
    surname = models.CharField(max_length=124, default="")
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    about = models.TextField(max_length=256, blank=True)
    phone = models.CharField(max_length=12, default="")
    github_url = models.CharField(max_length=100, blank=True)
    skills = models.ManyToManyField(Skill, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "name", "surname"]

    def save(self, *args, **kwargs):
        if not self.avatar:
            # Generate a random background color
            colors = [
                (100, 149, 237),
                (60, 179, 113),
                (255, 127, 80),
                (147, 112, 219),
                (255, 215, 0),
                (255, 99, 71),
                (0, 191, 255),
                (128, 0, 128),
                (46, 139, 87),
            ]
            bg_color = random.choice(colors)

            # Create a square image
            size = (200, 200)
            image = Image.new("RGB", size, color=bg_color)
            draw = ImageDraw.Draw(image)

            # Get first letter of name
            text = self.name[0].upper() if self.name else "?"

            # Try to load a font, fallback to default
            try:
                # Attempt to find a system font. This varies by OS.
                # On Windows, arial.ttf is common.
                font = ImageFont.truetype("arial.ttf", 100)
            except IOError:
                font = ImageFont.load_default()

            # Center the text
            w, h = draw.textbbox((0, 0), text, font=font)[2:]
            draw.text(
                ((size[0] - w) / 2, (size[1] - h) / 2), text, fill="white", font=font
            )

            # Save to a buffer
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")

            # Set the avatar field
            filename = f'avatar_{self.pk or "new"}.png'
            self.avatar.save(filename, ContentFile(buffer.getvalue()), save=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} {self.surname}"
