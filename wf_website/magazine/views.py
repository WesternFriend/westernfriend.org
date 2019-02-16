from django.views.generic import DetailView

from .models import MagazineDepartment


class MagazineDepartmentDetail(DetailView):
    model = MagazineDepartment
