from django.urls import path
from django.urls.resolvers import URLPattern

from . import views

# URL Configuration

urlpatterns = [
    path("hello/", views.say_hello),
    path("email/", views.send_email),
    path("hello/aggregate/", views.aggregate_hello),
]
