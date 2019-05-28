from django.urls import path

from .views import MagazineDepartmentDetail

urlpatterns = [
    path('department/<slug:slug>/', MagazineDepartmentDetail.as_view(), name='department-detail')
]
