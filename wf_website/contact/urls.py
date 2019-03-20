from django.urls import path
from .views import ContactDetail

urlpatterns = [path("<slug:slug>/", ContactDetail.as_view(), name="contact-detail")]
