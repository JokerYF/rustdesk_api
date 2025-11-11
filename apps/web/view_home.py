from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.client_apis.common import request_debug_log


@request_debug_log
@login_required(login_url='web_login')
def home(request):
    """
    Web 首页：登录保护，依赖 Django 认证态（request.user）

    :param request: Http 请求对象
    :type request: HttpRequest
    :return: 首页或重定向响应
    :rtype: HttpResponse
    """
    username = getattr(request.user, 'username', '') or request.user.get_username()
    return render(request, 'home.html', context={'username': username})
