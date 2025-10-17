from django.urls import path

from apps.client_apis import views

urlpatterns = [
    path('heartbeat', views.heartbeat),
    path('sysinfo', views.sysinfo),
    path('login', views.login),
    path('logout', views.logout),
    path('ab', views.ab),
    path('currentUser', views.current_user),
    path('users', views.users),
    path('peers', views.peers),
    path('time_test', views.time_test),
]
