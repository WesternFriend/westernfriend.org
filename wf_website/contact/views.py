from django.views.generic import DetailView

from .models import Contact


class ContactDetail(DetailView):
    model = Contact
