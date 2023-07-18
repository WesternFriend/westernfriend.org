from typing import TYPE_CHECKING
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _

# Avoic circular import
# only while type checking import user
# from .models import User
if TYPE_CHECKING:
    from .models import User  # pragma: no cover


class UserManager(BaseUserManager):
    """Custom user model manager where email is the unique identifiers for
    authentication instead of usernames.

    Source: https://testdriven.io/blog/django-custom-user-model/
    """

    def create_user(
        self,
        email: str,
        password: str,
        **extra_fields: dict[str, str | bool],
    ) -> "User":
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError(_("The Email must be set"))
        email = self.normalize_email(email)
        user: User = self.model(email=email, **extra_fields)  # type: ignore
        user.set_password(password)
        user.save()

        return user

    def create_superuser(
        self,
        email: str,
        password: str,
        **extra_fields: dict[str, str | bool],
    ) -> "User":
        """Create and save a superuser with the given email and password."""
        extra_fields["is_staff"] = True  # type: ignore
        extra_fields["is_superuser"] = True  # type: ignore
        extra_fields["is_active"] = True  # type: ignore

        return self.create_user(email, password, **extra_fields)
