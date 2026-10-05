from django.urls import path

from .views import CitaCreateView

urlpatterns = [
    path('citas/', CitaCreateView.as_view(), name='cita-create'),
]