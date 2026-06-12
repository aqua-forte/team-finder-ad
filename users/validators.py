from django.core.exceptions import ValidationError


def validate_github_url(value):
    """
    Validator to ensure the provided URL contains 'github.com'.
    """
    if value and "github.com" not in value:
        raise ValidationError("Ссылка должна вести на github.com")
