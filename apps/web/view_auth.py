import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect

from apps.client_apis.common import request_debug_log

# Create your views here.
logger = logging.getLogger(__name__)


@request_debug_log
def index(request):
    # cookies = request.COOKIES
    # print(cookies)
    # print(dict(cookies))
    # for key, value in cookies.items():
    #     print(f"{key}: {value}")
    # return JsonResponse({'message': 'Web正在开发中'})
    return render(request, 'login.html')


@request_debug_log
def login(request: HttpRequest):
    """
    处理登录请求：使用 Django 标准认证（authenticate/login），
    成功则跳转首页或 next 参数，失败则回到登录页并提示错误。

    :param request: Http 请求对象
    :type request: HttpRequest
    :return: 登录页面或首页的响应
    :rtype: HttpResponse
    """
    if request.method == 'GET':
        next_url = request.GET.get('next')
        # 若已存在认证态或未过期的自定义 session，则直接跳转
        if getattr(request, 'user', None) and request.user.is_authenticated:
            return redirect(next_url or 'web_home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next') or request.GET.get('next')
        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, '用户名或密码错误')
            return render(request, 'login.html', context={'next': next_url})
        auth_login(request, user)
        return redirect(next_url or 'web_home')
    else:
        next_url = request.GET.get('next')
        return render(request, 'login.html', context={'next': next_url})


@request_debug_log
@login_required(login_url='web_login')
def logout(request):
    auth_logout(request)
    return redirect('web_login')
