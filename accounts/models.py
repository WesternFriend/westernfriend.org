from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from subscription.models import Subscription


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

    subscriptions: models.QuerySet[Subscription]

    @property
    def is_subscriber(self) -> bool:
        """Check whether user has active subscription."""
        if not hasattr(self, "subscription"):
            return False

        return self.subscription.is_active
