from django.core.exceptions import ValidationError


def validate_github_url(value):
    """Проверяет, что предоставленный URL содержит 'github.com'."""
    if value and "github.com" not in value:
        raise ValidationError("Ссылка должна вести на github.com")
