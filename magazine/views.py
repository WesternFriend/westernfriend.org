from django.views.generic import DetailView

from .models import MagazineDepartment


class MagazineDepartmentDetail(DetailView):
    model = MagazineDepartment
    context_object_name = "department"

    template_name = "magazine/magazine_department_detail.html"
