from django.urls import path

from apps.web import view_auth, view_home

urlpatterns = [
    path('', view_auth.index),
    path('login', view_auth.login, name='web_login'),
    path('logout', view_auth.logout, name='web_logout'),
    path('home', view_home.home, name='web_home'),
    path('nav-content', view_home.nav_content, name='web_nav_content'),
    path('device/rename-alias', view_home.rename_alias, name='web_rename_alias'),
    path('device/detail', view_home.device_detail, name='web_device_detail'),
    path('device/update', view_home.update_device, name='web_device_update'),
    path('device/statuses', view_home.device_statuses, name='web_device_statuses'),
    path('user/update', view_home.update_user, name='web_user_update'),
    path('user/reset-password', view_home.reset_user_password, name='web_user_reset_password'),
]
