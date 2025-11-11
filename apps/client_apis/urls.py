from django.urls import path

from apps.client_apis import views, view_ab, view_audit

urlpatterns = [
    path('heartbeat', views.heartbeat),
    path('sysinfo', views.sysinfo),
    path('login', views.login),
    path('logout', views.logout),
    path('currentUser', views.current_user),
    path('users', views.users),
    path('peers', views.peers),
    path('ab', view_ab.ab),
    path('ab/personal', view_ab.ab_personal),
    path('ab/peer/add/<str:guid>', view_ab.ab_peer_add),
    path('ab/peer/update/<str:guid>', view_ab.ab_peer_update),
    path('ab/peer/<str:guid>', view_ab.ab_peer_delete),
    path('ab/tags/<str:guid>', view_ab.ab_tags),
    path('ab/tag/<str:guid>', view_ab.ab_tag),
    path('ab/tag/add/<str:guid>', view_ab.ab_tag_add),
    path('ab/tag/rename/<str:guid>', view_ab.ab_tag_rename),
    path('ab/tag/update/<str:guid>', view_ab.ab_tag_add),
    path('ab/settings', view_ab.ab_settings),
    path('ab/shared/profiles', view_ab.ab_shared_profiles),
    path('ab/peers', view_ab.ab_peers),
    path('device-group/accessible', views.device_group_accessible),
    path('audit/conn', view_audit.audit_conn),
    path('audit/file', view_audit.audit_file),
    path('time', views.time_test),
]
