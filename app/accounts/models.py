import datetime

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    # source: https://testdriven.io/blog/django-custom-user-model/
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    def get_active_subscription(self):
        """Get subscription that isn't expired for this user."""
        today = datetime.datetime.today()

        try:
            active_subscription = self.subscriptions.get(end_date__gte=today)
        except ObjectDoesNotExist:
            return None

        return active_subscription

    @property
    def is_subscriber(self):
        """Check whether user has active subscription."""

        if self.get_active_subscription() is not None:
            return True

        return False
