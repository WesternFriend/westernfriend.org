from django.views.generic import DetailView

from .models import Author


class AuthorDetail(DetailView):
    model = Author

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context
