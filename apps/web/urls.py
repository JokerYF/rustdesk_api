from django.urls import path

from apps.web import view_auth, view_home

urlpatterns = [
    path('', view_auth.index),
    path('login', view_auth.login, name='web_login'),
    path('logout', view_auth.logout, name='web_logout'),
    path('home', view_home.home, name='web_home'),
]
