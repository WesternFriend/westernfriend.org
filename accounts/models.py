from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from subscription.models import Subscription


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


class User(AbstractUser):
    # email must be unique since it is used as the username field
    email = models.EmailField(unique=True)
    # disable username field
    username = None  # type: ignore

    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"

    # The field named as the 'USERNAME_FIELD' for a custom user model
    # must not be included in 'REQUIRED_FIELDS'.
    # HINT: The 'USERNAME_FIELD' is currently set to 'email',
    # you should remove 'email' from the 'REQUIRED_FIELDS'.
    REQUIRED_FIELDS = []

    objects = UserManager()  # type: ignore

    subscriptions: models.QuerySet[Subscription]

    @property
    def is_subscriber(self) -> bool:
        """Check whether user has active subscription."""
        if not hasattr(self, "subscription"):
            return False

        return self.subscription.is_active
