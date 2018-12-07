from django.views.generic import DetailView

from .models import Author


class AuthorDetail(DetailView):
    model = Author