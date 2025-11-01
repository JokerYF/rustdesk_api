from django.urls import path

from apps.web import views

urlpatterns = [
    path('', views.index)
]
