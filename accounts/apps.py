from django.apps import AppConfig
from wagtail.users.apps import WagtailUsersAppConfig


class AccountsConfig(AppConfig):
    name = "accounts"


class CustomUsersAppConfig(WagtailUsersAppConfig):
    user_viewset = "accounts.viewsets.UserViewSet"
