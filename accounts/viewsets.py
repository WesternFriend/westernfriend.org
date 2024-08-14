from wagtail.users.views.users import UserViewSet as WagtailUserViewSet
from .forms import CustomUserEditForm, CustomUserCreationForm


class UserViewSet(WagtailUserViewSet):
    list_export = ["id", "username", "email", "first_name", "last_name", "is_active"]
    export_filename = "westernfriend.org-users"

    def get_form_class(self, for_update=False):
        if for_update:
            return CustomUserEditForm
        return CustomUserCreationForm
