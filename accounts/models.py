from django.db import models

from authtools.models import AbstractEmailUser


class User(AbstractEmailUser):
    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
