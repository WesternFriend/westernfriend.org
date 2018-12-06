from django.urls import path
from .views import AuthorDetail

urlpatterns = [
    path('<slug:slug>/', AuthorDetail.as_view(), name='author-detail')
]