import datetime

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from subscription.models import Subscription

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    # source: https://testdriven.io/blog/django-custom-user-model/
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    subscriptions: models.QuerySet[Subscription]

    def __str__(self) -> str:
        return self.email

    # TODO: refactor this to `get_active_subscriptions`
    # and return a list of active subscriptions
    # so we can allow use-cases where a user can have multiple active subscriptions
    # such as managing subscriptions for a Meeting or a Group
    def get_active_subscription(self) -> Subscription | None:
        """Get subscription that isn't expired for this user."""
        today = datetime.datetime.today()

        # using filter.first() instead of get() because get() throws an exception
        # if there are multiple active subscriptions
        # TODO: determine how to handle multiple active subscriptions
        return self.subscriptions.filter(
            end_date__gte=today,
            paid=True,
        ).first()

    @property
    def is_subscriber(self) -> bool:
        """Check whether user has active subscription."""

        if self.get_active_subscription() is not None:
            return True

        return False
