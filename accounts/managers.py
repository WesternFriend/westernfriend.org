from typing import TYPE_CHECKING
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _

# Avoic circular import
# only while type checking import user
# from .models import User
if TYPE_CHECKING:
    from .models import User


class UserManager(BaseUserManager):
    """Custom user model manager where email is the unique identifiers for
    authentication instead of usernames.

    Source: https://testdriven.io/blog/django-custom-user-model/
    """

    def create_user(
        self,
        email: str,
        password: str,
        **extra_fields,
    ) -> "User":
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError(_("The Email must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(
        self,
        email: str,
        password: str,
        **extra_fields,
    ) -> "User":
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(email, password, **extra_fields)
