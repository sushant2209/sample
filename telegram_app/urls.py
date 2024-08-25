# myapp/urls.py
from django.urls import path
from .views import fetch_and_update

urlpatterns = [
    path('fetch-update/', fetch_and_update, name='fetch_and_update'),
]
