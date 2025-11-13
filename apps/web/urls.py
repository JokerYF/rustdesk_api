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
    # 地址簿相关路由
    path('personal/list', view_home.get_personal_list, name='web_personal_list'),
    path('personal/create', view_home.create_personal, name='web_personal_create'),
    path('personal/delete', view_home.delete_personal, name='web_personal_delete'),
    path('personal/rename', view_home.rename_personal, name='web_personal_rename'),
    path('personal/detail', view_home.personal_detail, name='web_personal_detail'),
    path('personal/add-device', view_home.add_device_to_personal, name='web_personal_add_device'),
    path('personal/remove-device', view_home.remove_device_from_personal, name='web_personal_remove_device'),
]
