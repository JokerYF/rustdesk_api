import time

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods

from apps.client_apis.common import request_debug_log
from apps.db.service import UserService


@request_debug_log
@require_http_methods(['POST'])
@login_required(login_url='web_login')
def update_user(request: HttpRequest) -> JsonResponse:
    """
    更新用户基础信息（仅限管理员）

    :param request: POST，包含 username, full_name(可选), email(可选), is_staff(可选: '1'/'0')
    :return: {"ok": true}
    """
    if not request.user.is_staff:
        return JsonResponse({'ok': False, 'err_msg': '无权限'}, status=403)
    username = (request.POST.get('username') or '').strip()
    if not username:
        return JsonResponse({'ok': False, 'err_msg': '参数错误'}, status=400)
    user = User.objects.filter(username=username).first()
    if not user:
        return JsonResponse({'ok': False, 'err_msg': '用户不存在'}, status=404)
    full_name = (request.POST.get('full_name') or '').strip()
    email = (request.POST.get('email') or '').strip()
    is_staff_raw = request.POST.get('is_staff')

    # 更新字段列表
    update_fields = []

    if full_name != '':
        # 仅使用 first_name 存储展示用姓名
        user.first_name = full_name
        user.last_name = ''
        update_fields.extend(['first_name', 'last_name'])
    if email != '':
        user.email = email
        update_fields.append('email')

    # 不允许用户修改自己的管理员权限
    if is_staff_raw is not None:
        if username == request.user.username:
            return JsonResponse({'ok': False, 'err_msg': '不能修改自己的管理员权限'}, status=400)
        user.is_staff = (str(is_staff_raw).strip() == '1')
        update_fields.append('is_staff')

    if update_fields:
        user.save(update_fields=update_fields)
    return JsonResponse({'ok': True})


@request_debug_log
@require_http_methods(['POST'])
@login_required(login_url='web_login')
def reset_user_password(request: HttpRequest) -> JsonResponse:
    """
    重置用户密码（仅限管理员）

    :param request: POST，包含 username, password1, password2
    :return: {"ok": true}
    """
    if not request.user.is_staff:
        return JsonResponse({'ok': False, 'err_msg': '无权限'}, status=403)
    username = (request.POST.get('username') or '').strip()
    password1 = (request.POST.get('password1') or '').strip()
    password2 = (request.POST.get('password2') or '').strip()
    if not username or not password1 or not password2:
        return JsonResponse({'ok': False, 'err_msg': '参数错误'}, status=400)
    if password1 != password2:
        return JsonResponse({'ok': False, 'err_msg': '两次密码不一致'}, status=400)
    if len(password1) < 6:
        return JsonResponse({'ok': False, 'err_msg': '密码长度至少为6位'}, status=400)
    user = User.objects.filter(username=username).first()
    if not user:
        return JsonResponse({'ok': False, 'err_msg': '用户不存在'}, status=404)
    user.set_password(password1)
    user.save(update_fields=['password'])
    return JsonResponse({'ok': True})


@request_debug_log
@require_http_methods(['POST'])
@login_required(login_url='web_login')
def delete_user(request: HttpRequest) -> JsonResponse:
    """
    删除用户（软删除，将is_active置为False，仅限管理员）

    :param request: POST，包含 username
    :return: {"ok": true}
    """
    if not request.user.is_staff:
        return JsonResponse({'ok': False, 'err_msg': '无权限'}, status=403)
    username = (request.POST.get('username') or '').strip()
    if not username:
        return JsonResponse({'ok': False, 'err_msg': '参数错误'}, status=400)
    # 不能删除自己
    if username == request.user.username:
        return JsonResponse({'ok': False, 'err_msg': '不能删除自己'}, status=400)
    user = User.objects.filter(username=username, is_active=True).first()
    if not user:
        return JsonResponse({'ok': False, 'err_msg': '用户不存在或已被删除'}, status=404)
    # 软删除：将is_active置为False
    user.is_active = False
    new_name = user.username
    user.username = new_name + f'_deleted_{time.time()}'
    update_fields = ['username', 'is_active']
    if email := user.email:
        user.email = email + f'_deleted_{time.time()}'
        update_fields.append('email')
    user.save(update_fields=update_fields)
    return JsonResponse({'ok': True})


@request_debug_log
@require_http_methods(['POST'])
@login_required(login_url='web_login')
def create_user(request: HttpRequest) -> JsonResponse:
    """
    创建新用户（仅限管理员）

    :param request: POST，包含 username, password1, password2, full_name(可选), email(可选), is_staff(可选: '1'/'0')
    :return: {"ok": true}
    """
    if not request.user.is_staff:
        return JsonResponse({'ok': False, 'err_msg': '无权限'}, status=403)

    username = (request.POST.get('username') or '').strip()
    password1 = (request.POST.get('password1') or '').strip()
    password2 = (request.POST.get('password2') or '').strip()
    full_name = (request.POST.get('full_name') or '').strip()
    email = (request.POST.get('email') or '').strip()
    is_staff_raw = request.POST.get('is_staff')

    # 参数校验
    if not username or not password1 or not password2:
        return JsonResponse({'ok': False, 'err_msg': '用户名和密码不能为空'}, status=400)
    if password1 != password2:
        return JsonResponse({'ok': False, 'err_msg': '两次密码不一致'}, status=400)
    if len(password1) < 6:
        return JsonResponse({'ok': False, 'err_msg': '密码长度至少为6位'}, status=400)

    # 检查用户名是否已存在（包括软删除的用户）
    if User.objects.filter(username=username).exists():
        return JsonResponse({'ok': False, 'err_msg': '用户名已存在'}, status=400)

    # 检查邮箱是否已存在（如果提供了邮箱）
    if email and User.objects.filter(email=email).exists():
        return JsonResponse({'ok': False, 'err_msg': '邮箱已被使用'}, status=400)

    # 确定管理员权限
    is_staff = (str(is_staff_raw).strip() == '1') if is_staff_raw is not None else False

    try:
        # 使用 UserService 创建用户
        user_service = UserService()
        user = user_service.create_user(
            username=username,
            password=password1,
            email=email,
            is_staff=is_staff,
            is_superuser=False,
            is_active=True,
            group=None  # 暂不指定组
        )

        # 如果提供了姓名，则更新
        if full_name:
            user.first_name = full_name
            user.last_name = ''
            user.save(update_fields=['first_name', 'last_name'])

        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'err_msg': f'创建用户失败: {str(e)}'}, status=500)
