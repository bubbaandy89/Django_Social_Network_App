from pathlib import Path
from typing import Optional

import magic
from django.conf import settings
from django.core import mail
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.http import url_has_allowed_host_and_scheme


def _get_mime_type(filepath: Path) -> str:
    mime: magic.Magic = magic.Magic(mime=True)
    return mime.from_file(filepath)


def send_welcome_email(user_email: str, username: str, profile_url: str) -> int:
    context: dict[str, str] = {
        "email": user_email,
        "username": username,
        "profile_url": profile_url,
    }

    html_message: str = render_to_string("users/welcome_email.html", context)

    return mail.send_mail(
        subject=f"Welcome to {settings.SITE_NAME}!",
        message=strip_tags(html_message),
        from_email=None,  # Uses DEFAULT_FROM_EMAIL setting
        recipient_list=[user_email],
        html_message=html_message,
    )


def new_user_created_email(user_email: str, username: str, profile_url: str) -> int:
    context: dict[str, str] = {
        "email": user_email,
        "username": username,
        "profile_url": profile_url,
    }

    html_message: str = render_to_string("users/new_user_admins_email.html", context)

    return mail.send_mail(
        subject=f"New user needs verification at {settings.SITE_NAME}!",
        message=strip_tags(html_message),
        from_email=None,  # Uses DEFAULT_FROM_EMAIL setting
        recipient_list=settings.EMAIL_ADMIN_RECIPIENTS,
        html_message=html_message,
    )


def balance_user_profiles() -> None:
    from django.contrib.auth.models import User

    from users.models import Profile

    for user in User.objects.all():
        try:
            Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            print(f"{user.username} is missing a profile")
            user.delete()


class URLValidator:
    @staticmethod
    def validate_redirect(url: Optional[str], request: HttpRequest) -> str:
        """
        Validates a redirect URL to prevent open redirect vulnerabilities.

        Args:
            url: URL to validate
            request: Current request object

        Returns:
            str: Safe URL to redirect to
        """
        if not url:
            return settings.DEFAULT_REDIRECT_URL

        # Check if URL is safe using Django's built-in validator
        is_safe: bool = url_has_allowed_host_and_scheme(
            url=url,
            allowed_hosts={request.get_host()},
            require_https=settings.SECURE_SSL_REDIRECT,
        )

        return url if is_safe else settings.DEFAULT_REDIRECT_URL
