from wagtail.users.views.users import UserViewSet as WagtailUserViewSet


class UserViewSet(WagtailUserViewSet):
    list_export = ["id", "username", "email", "first_name", "last_name", "is_active"]
    export_filename = "westernfriend.org-users"
