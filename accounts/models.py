import datetime

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

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
        """
        Get subscription for this user that isn't expired.
        """
        today = datetime.datetime.today()

        return self.subscriptions.get(end_date__gte=today)

    @property
    def is_subscriber(self):
        """
        Check whether user has active subscription.
        """

        if self.get_active_subscription() is not None:
            return True

        return False
