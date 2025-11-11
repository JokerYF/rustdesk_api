import json
import logging
import traceback

from django.contrib.auth.models import User
from django.http import HttpRequest, JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.client_apis.common import check_login, request_debug_log, debug_request_None
from apps.db.models import PeerInfo
from apps.db.service import HeartBeatService, PeerInfoService, TokenService, UserService, \
    LoginClientService
from common.utils import get_local_time

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
@request_debug_log
def heartbeat(request: HttpRequest):
    request_data = json.loads(request.body.decode('utf-8'))
    uuid = request_data.get('uuid')
    peer_id = request_data.get('id')
    modified_at = request_data.get('modified_at', get_local_time())
    ver = request_data.get('ver')

    HeartBeatService().update(
        uuid=uuid,
        peer_id=peer_id,
        modified_at=modified_at,
        ver=ver,
    )
    return HttpResponse(status=200)


@require_http_methods(["POST"])
@request_debug_log
def sysinfo(request: HttpRequest):
    body = json.loads(request.body.decode('utf-8'))
    uuid = body.get('uuid')

    # 先更新设备信息
    PeerInfoService().update(
        uuid=uuid,
        peer_id=body.get('id'),
        cpu=body.get('cpu'),
        device_name=body.get('hostname'),
        memory=body.get('memory'),
        os=body.get('os'),
        username=body.get('username'),
        version=body.get('version'),
    )

    # 如果当前设备登录过，则更新token
    # 这里有个问题，这里更新没有校验token有效期，服务器停机好几个小时后启动，还是会刷新token，没想好这块逻辑，先这样
    TokenService(request=request).update_token_by_uuid(uuid)

    return HttpResponse(status=200)


@require_http_methods(["POST"])
@request_debug_log
def login(request: HttpRequest):
    """
    处理用户登录请求
    :param request: HTTP请求对象
    :return: JSON响应对象
    """
    token_service = TokenService(request=request)
    body = token_service.request_body

    username = body.get('username')
    password = body.get('password')
    uuid = body.get('uuid')
    device_info = body.get('deviceInfo', {})
    platform = device_info.get('os')  # 设备端别
    client_type = device_info.get('type')
    client_name = device_info.get('name')

    try:
        user = UserService().get_user_by_name(username=username)
        assert user.check_password(password)
    except (User.DoesNotExist, AssertionError):
        logger.error(traceback.format_exc())
        return JsonResponse({'error': '用户名或密码错误'})

    token = token_service.create_token(username, uuid)

    # Server端记录登录信息
    LoginClientService().update_login_status(
        uuid=uuid,
        username=user,
        peer_id=body.get('id'),
        client_name=client_name,
        platform=platform,
        client_type=client_type,
    )
    #
    # LogService().create_log(
    #     username=username,
    #     uuid=uuid,
    #     log_type='login',
    #     log_message=f'用户 {username} 登录'
    # )

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
@request_debug_log
@check_login
def logout(request: HttpRequest):
    token_service = TokenService(request=request)
    token = token_service.authorization
    user_info = token_service.user_info
    body = token_service.request_body

    uuid = body.get('uuid')

    token_service.delete_token(token)

    # 更新登出状态
    LoginClientService().update_logout_status(
        uuid=uuid,
        username=user_info,
        peer_id=body.get('id'),
    )
    #
    # LogService().create_log(
    #     username=user_info,
    #     uuid=uuid,
    #     log_type='logout',
    #     log_message=f'用户 {user_info} 退出登录'
    # )
    return JsonResponse({'code': 1})


@require_http_methods(["POST"])
@request_debug_log
@check_login
def current_user(request: HttpRequest):
    """
    获取当前用户信息
    :param request:
    :return:
    """
    token_service = TokenService(request=request)
    token = token_service.authorization
    user_info = token_service.user_info

    return JsonResponse(
        {
            'name': user_info.username,
            'access_token': token,
            'type': 'access_token',
        }
    )


@require_http_methods(["GET"])
@request_debug_log
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
    token_service = TokenService(request=request)
    user_info = token_service.user_info
    if user_info.is_superuser:
        result = UserService().get_list_by_status(status=status, page=page, page_size=page_size)['results']
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
@request_debug_log
@check_login
def peers(request: HttpRequest):
    """
    展示当前用户可以看到的设备信息
    当前如果是管理员，则可以看到全部（包括未登录的设备）
    如果是用户，则默认只能看到自己登录的设备
    :param request:
    :return:
    """
    # TODO 这里有一个问题，这里需要按照用户展示设备信息，当前只展示登录用户的信息

    token_service = TokenService(request=request)
    user_info = token_service.user_info
    # uuid = token_service.get_cur_uuid_by_token(token)

    client_list = PeerInfoService().get_list()
    data = []
    for client in client_list:
        # if client.uuid == uuid:
        #     continue
        data.append(
            {
                "id": client.peer_id,
                "info": {
                    "device_name": client.device_name,
                    "os": client.os,
                    "username": client.username,
                },
                "status": 1,
                "user_name": user_info.username,
            }
        )
    result = {
        'total': len(client_list),
        'data': data
    }
    return JsonResponse(result)


@require_http_methods(["GET"])
@request_debug_log
@debug_request_None  # 官方对于设备组有权限控制，目前无法控制，直接返回None，接口不报错即可
@check_login
def device_group_accessible(request):
    """
    admin获取当前服务端所有设备信息
    :param request:
    :return:
    """
    token_service = TokenService(request=request)
    user_info = token_service.user_info

    client_list = PeerInfoService().get_list()
    data = []
    for client in client_list:
        client = client if isinstance(client, PeerInfo) else client.uuid
        # if client.uuid == uuid:
        #     continue
        data.append(
            {
                "id": client.peer_id,
                "info": {
                    "device_name": client.device_name,
                    "os": client.os,
                    "username": client.username,
                },
                "status": 1,
                "user_name": user_info.username,
            }
        )
    result = {
        'total': len(client_list),
        'data': data
    }
    return JsonResponse(result)
