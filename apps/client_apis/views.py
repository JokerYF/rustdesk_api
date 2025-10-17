import json
import json
import logging

from django.contrib.auth.models import User
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.client_apis.common import check_login
from apps.common.utils import get_local_time
from apps.db.service import HeartBeatService, SystemInfoService, TokenService, UserService, LoginLogService, \
    LoginClientService

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def time_test(request: HttpRequest):
    """
    测试时间存储是否使用服务器本地时间

    :param request: HTTP请求对象
    :return: 包含当前时间和时区信息的JSON响应
    """
    now = timezone.now()
    local_time = timezone.localtime(now)

    return JsonResponse({
        'utc_time': now.isoformat(),
        'local_time': local_time.isoformat(),
        'timezone': str(local_time.tzinfo)
    })


@require_http_methods(["POST"])
def heartbeat(request: HttpRequest):
    request_data = json.loads(request.body.decode('utf-8'))
    uuid = request_data.get('uuid')
    client_id = request_data.get('id')
    modified_at = request_data.get('modified_at', get_local_time())
    ver = request_data.get('ver')

    TokenService().update_token_by_uuid(uuid)
    HeartBeatService().update(
        uuid=uuid,
        client_id=client_id,
        modified_at=modified_at,
        ver=ver,
    )
    return JsonResponse({'status': 'ok'})


@require_http_methods(["POST"])
def sysinfo(request: HttpRequest):
    request_body = json.loads(request.body.decode('utf-8'))
    uuid = request_body.get('uuid')

    SystemInfoService().update(
        uuid=uuid,
        client_id=request_body.get('id'),
        cpu=request_body.get('cpu'),
        device_name=request_body.get('hostname'),
        memory=request_body.get('memory'),
        os=request_body.get('os'),
        username=request_body.get('username'),
        version=request_body.get('version'),
    )
    return JsonResponse({'status': 'ok'})


@require_http_methods(["POST"])
def login(request: HttpRequest):
    """
    处理用户登录请求
    
    :param request: HTTP请求对象
    :return: JSON响应对象
    """
    logger.debug(f'login post_body: {request.body}')
    request_body = json.loads(request.body.decode('utf-8'))
    username = request_body.get('username')
    password = request_body.get('password')
    uuid = request_body.get('uuid')

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist as e:
        return JsonResponse({'error': '用户名或密码错误'})

    # 使用check_password方法验证密码
    if not user.check_password(password):
        return JsonResponse({'error': '用户名或密码错误'})

    token = TokenService().create_token(username, uuid)

    # Server端记录登录信息
    LoginClientService().update_login_status(
        uuid=uuid,
        username=username,
    )

    # 创建登录日志
    login_log_service = LoginLogService()
    login_log_service.create(
        username=username,
        uuid=uuid,
        client_id=request_body.get('id'),
        login_type=request_body.get('login_type', 'access_token'),
        login_status=True,
        os=request_body['deviceInfo'].get('os'),
        device_type=request_body['deviceInfo'].get('type'),
        device_name=request_body['deviceInfo'].get('name'),
    )

    return JsonResponse(
        {
            'access_token': token,
            'type': 'access_token',
            'user': {
                'name': username,
            }
        }
    )


@require_http_methods(["POST"])
def logout(request: HttpRequest):
    request_body = json.loads(request.body.decode('utf-8'))
    # print(request_body)
    token = request.headers.get('Authorization')[7:]
    uuid = request_body.get('uuid')

    token_service = TokenService()
    username = token_service.get_user_info_by_token(token)
    token_service.delete_token(token)

    # 更新登出状态
    LoginClientService().update_logout_status(
        uuid=uuid,
        username=username,
    )

    login_log_service = LoginLogService()
    login_log = login_log_service.get_login_log(uuid=uuid, username=username)
    login_log_service.create(
        username=username,
        uuid=uuid,
        client_id=login_log.client_id,
        login_type=login_log.login_type,
        login_status=False,
        os=login_log.os,
        device_type=login_log.device_type,
        device_name=login_log.device_name,
    )
    return JsonResponse({'code': 1})


@require_http_methods(["GET", "POST"])
@check_login
def ab(request: HttpRequest):
    """
    获取地址簿
    :param request:
    :return:
    """
    if request.method == 'GET':
        return JsonResponse({'error': 'None'})
    elif request.method == 'POST':
        request_body = json.loads(request.body.decode('utf-8'))
        print(request_body)
    return JsonResponse({'error': 'None'})


@require_http_methods(["POST"])
@check_login
def current_user(request: HttpRequest):
    """
    获取当前用户信息
    :param request:
    :return:
    """
    token_service = TokenService()
    token = request.headers.get('Authorization')[7:]

    user_info = token_service.get_user_info_by_token(token)

    return JsonResponse(
        {
            'name': user_info.username,
            'access_token': token,
            'type': 'access_token',
        }
    )


@require_http_methods(["GET"])
@check_login
def users(request: HttpRequest):
    """
    获取所有用户信息
    :param request:
    :return:
    """
    page = int(request.GET.get('current', 1))
    page_size = int(request.GET.get('pageSize', 10))
    status = int(request.GET.get('status', 1))
    user_info = TokenService().get_user_info_by_token(request.headers.get('Authorization')[7:])
    if user_info.is_superuser:
        result = UserService().get_list(status=status, page=page, page_size=page_size)['results']
    else:
        result = [user_info]

    user_list = [
        {
            "name": user.username,
            "email": user.email,
            "note": "",
            "is_admin": user.is_superuser,
            "status": user.is_active,
            "info": {}
        } for user in result
    ]

    return JsonResponse(
        {
            'total': len(user_list),
            'data': user_list
        }
    )


@require_http_methods(["GET"])
@check_login
def peers(request: HttpRequest):
    """
    展示当前用户可以看到的设备信息
    当前如果是管理员，则可以看到全部（包括未登录的设备）
    如果是用户，则默认只能看到自己登录的设备
    :param request:
    :return:
    """
    page = int(request.GET.get('current', 1))
    page_size = int(request.GET.get('pageSize', 10))

    token = request.headers.get('Authorization')[7:]
    token_service = TokenService()
    user_info = token_service.get_user_info_by_token(token)
    uuid = token_service.get_cur_uuid_by_token(token)

    if user_info.is_superuser:
        client_list = SystemInfoService().get_list(page=page, page_size=page_size)
    else:
        client_list = LoginClientService().get_login_client_list(user_info.username)
    return JsonResponse(
        {
            'total': len(client_list),
            'data': [
                {
                    "id": client.client_id,
                    "info": {
                        "device_name": client.device_name,
                        "os": client.os,
                        "username": client.username,
                    },
                } for client in client_list['results'] if client.uuid != uuid
            ]
        }
    )
