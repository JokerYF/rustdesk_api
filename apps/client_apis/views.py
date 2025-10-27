import json
import logging
import traceback

from django.contrib.auth.models import User
from django.http import HttpRequest, JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.client_apis.common import check_login, request_debug_log
from apps.common.utils import get_local_time
from apps.db.models import SystemInfo
from apps.db.service import HeartBeatService, SystemInfoService, TokenService, UserService, \
    LoginClientService, TagService, LogService, AuditConnService

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
    client_id = request_data.get('id')
    modified_at = request_data.get('modified_at', get_local_time())
    ver = request_data.get('ver')

    HeartBeatService().update(
        uuid=uuid,
        client_id=client_id,
        modified_at=modified_at,
        ver=ver,
    )
    return JsonResponse({'status': 'ok'})


@require_http_methods(["POST"])
@request_debug_log
def sysinfo(request: HttpRequest):
    body = json.loads(request.body.decode('utf-8'))
    uuid = body.get('uuid')

    # 先更新设备信息
    SystemInfoService().update(
        uuid=uuid,
        client_id=body.get('id'),
        cpu=body.get('cpu'),
        device_name=body.get('hostname'),
        memory=body.get('memory'),
        os=body.get('os'),
        username=body.get('username'),
        version=body.get('version'),
    )

    # 如果当前设备登录过，则更新token
    TokenService().update_token_by_uuid(uuid)

    return JsonResponse({'status': 'ok'})


@require_http_methods(["POST"])
@request_debug_log
def login(request: HttpRequest):
    """
    处理用户登录请求
    :param request: HTTP请求对象
    :return: JSON响应对象
    """
    body = json.loads(request.body.decode('utf-8'))
    username = body.get('username')
    password = body.get('password')
    uuid = body.get('uuid')

    try:
        user = User.objects.get(username=username)
        assert user.check_password(password)
    except User.DoesNotExist as e:
        logger.error(traceback.format_exc())
        return JsonResponse({'error': '用户名或密码错误'})

    token = TokenService().create_token(username, uuid)

    # Server端记录登录信息
    LoginClientService().update_login_status(
        uuid=SystemInfoService().get_client_info_by_uuid(uuid),
        username=user,
        client_id=body.get('id'),
    )

    LogService().create_log(
        username=username,
        uuid=uuid,
        log_type='login',
        log_message=f'用户 {username} 登录'
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
@request_debug_log
@check_login
def logout(request: HttpRequest):
    body = json.loads(request.body.decode('utf-8'))
    uuid = body.get('uuid')
    token_service = TokenService()
    token, user_info, body = token_service.get_request_info(request)
    token_service.delete_token(token)

    # 更新登出状态
    LoginClientService().update_logout_status(
        uuid=uuid,
        username=user_info,
        client_id=body.get('id'),
    )

    LogService().create_log(
        username=user_info,
        uuid=uuid,
        log_type='logout',
        log_message=f'用户 {user_info} 退出登录'
    )
    return JsonResponse({'code': 1})


@require_http_methods(["GET", "POST"])
@request_debug_log
@check_login
def ab(request: HttpRequest):
    """
    获取地址簿
    :param request:
    :return:
    """
    if request.method == 'GET':
        # return JsonResponse({'error': 'None'})
        return JsonResponse(
            {
                "data": json.dumps(
                    {
                        'peers': [],
                        'tags': [],
                        'tag_colors': {},
                    }
                )
            }
        )
    elif request.method == 'POST':
        token_service = TokenService()
        token, user_info, body = token_service.get_request_info(request)
        body = json.loads(request.body.decode('utf-8'))
        data = json.loads(body.get('data')) if body.get('data') else {}

        tag_service = TagService(user_info)
        try:
            if tags := data.get('tags', []):
                for tag in tags:
                    color = json.loads(data['tag_colors'])[tag]
                    tag_service.create_tag(tag, color)
        except Exception as e:
            logger.error(traceback.format_exc())
            return JsonResponse({'error': f'创建标签失败: {e}'})

    return JsonResponse({'code': 1})


@require_http_methods(["POST"])
@request_debug_log
@check_login
def ab_personal(request: HttpRequest):
    """
    获取个人地址簿
    :param request:
    :return:
    """
    token_service = TokenService()
    token, user_info, body = token_service.get_request_info(request)
    user_service = UserService()
    return JsonResponse(
        {
            "guid": user_service.get_guid(user_info),
            "name": user_info.username,
            "rule": 3
        }
    )


@require_http_methods(["POST"])
@request_debug_log
@check_login
def current_user(request: HttpRequest):
    """
    获取当前用户信息
    :param request:
    :return:
    """
    token_service = TokenService()
    token, user_info, body = token_service.get_request_info(request)

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
    token_service = TokenService()
    token, user_info, body = token_service.get_request_info(request)
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
    page = int(request.GET.get('current', 1))
    page_size = int(request.GET.get('pageSize', 10))

    token_service = TokenService()
    token, user_info, body = token_service.get_request_info(request)
    uuid = token_service.get_cur_uuid_by_token(token)

    if user_info.is_superuser:
        client_list = SystemInfoService().get_list(page=page, page_size=page_size)['results']
    else:
        client_list = LoginClientService().get_login_client_list(user_info)
    data = []
    for client in client_list:
        client = client if isinstance(client, SystemInfo) else client.uuid
        if client.uuid == uuid:
            continue
        data.append(
            {
                "id": client.client_id,
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
@check_login
def device_group_accessible(request):
    """
    admin获取当前服务端所有设备信息
    :param request:
    :return:
    """
    page = int(request.GET.get('current', 1))
    page_size = int(request.GET.get('pageSize', 10))

    token_service = TokenService()
    token, user_info, body = token_service.get_request_info(request)
    uuid = token_service.get_cur_uuid_by_token(token)

    if user_info.is_superuser:
        client_list = SystemInfoService().get_list(page=page, page_size=page_size)['results']
    else:
        # client_list = LoginClientService().get_login_client_list(user_info.username)
        return JsonResponse(
            {
                'total': 0,
                'data': []
            }
        )

    data = []
    for client in client_list:
        client = client if isinstance(client, SystemInfo) else client.uuid
        # if client.uuid == uuid:
        #     continue
        data.append(
            {
                "id": client.client_id,
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


@require_http_methods(["POST"])
@request_debug_log
def audit_conn(request: HttpRequest):
    """
    连接日志
    :param request:
    :return:
    """
    body = json.loads(request.body)
    action = body.get('action')
    conn_id = body.get('conn_id')
    ip = body.get('ip', '')
    controlled_uuid = body.get('uuid')
    session_id = body.get('session_id')
    peer = body.get('peer')

    audit_service = AuditConnService()
    if action:
        audit_service.create_log(
            action=action,
            conn_id=conn_id,
            initiating_ip=ip,
            # controller_uuid=uuid,
            controlled_uuid=controlled_uuid,
            session_id=session_id
        )
        if action == 'close':
            add_log = audit_service.get(conn_id, action='new')
            audit_service.update(
                filters={
                    'action': action,
                    'conn_id': conn_id
                }, username=UserService().get_username(add_log.username)
            )
    else:
        system_info = SystemInfoService()
        audit_service.update_log(
            conn_id=conn_id,
            initiating_ip=ip,
            controller_uuid=system_info.get_client_info_by_client_id(peer[0]),
            controlled_uuid=controlled_uuid,
            session_id=session_id,
            _type=int(body.get('type')),
            username=str(peer[1]).lower() if peer else None
        )

    return JsonResponse(
        {
            'code': 1,
            'data': {
                'status': 1,
                'message': 'success'
            }
        }
    )


@require_http_methods(["POST"])
@request_debug_log
def audit_file(request):
    """
    文件日志
    :param request:
    :return:
    """
    # {"id":"488591401","info":"{\\"files\\":[[\\"\\",52923]],\\"ip\\":\\"172.16.41.91\\",\\"name\\":\\"Admin\\",\\"num\\":1}","is_file":true,"path":"C:\\\\Users\\\\Joker\\\\Downloads\\\\api_swagger.json","peer_id":"1508540501","type":1,"uuid":"MjI5MzdiMDAtNjExNy00OTVmLWFjNWUtNGM2MTc2NTE1Zjdl"}
    # {"id":"488591401","info":"{\\"files\\":[[\\"\\",801524]],\\"ip\\":\\"172.16.41.91\\",\\"name\\":\\"Admin\\",\\"num\\":1}","is_file":true,"path":"C:\\\\Users\\\\Joker\\\\Downloads\\\\782K.ofd","peer_id":"1508540501","type":0,"uuid":"MjI5MzdiMDAtNjExNy00OTVmLWFjNWUtNGM2MTc2NTE1Zjdl"}

    return JsonResponse(
        {
            'code': 1,
            'data': {
                'status': 1,
                'message': 'success'
            }
        }
    )


@require_http_methods(["POST"])
@request_debug_log
@check_login
def ap_peers(request):
    return JsonResponse(
        {
            'code': 1,
            'data': {
                'status': 1,
                'message': 'success'
            }
        }
    )


@require_http_methods(["POST"])
@request_debug_log
@check_login
def ab_tags(request, guid):
    token_service = TokenService()
    token, user_info, body = token_service.get_request_info(request)

    tag_service = TagService(user_info)
    tags = tag_service.get_all_tags()
    data = [
        {
            'name': tag.tag_id.tag,
            'color': int(tag.tag_id.color),
            'type': tag.tag_id.tag_type,
        } for tag in tags
    ]
    return JsonResponse(data, safe=False, status=200)


@require_http_methods(["POST"])
@request_debug_log
@check_login
def ab_tag_add(request, guid):
    body = json.loads(request.body)
    tag = body.get('name')
    color = body.get('color')

    token_service = TokenService()
    token, user_info, body = token_service.get_request_info(request)
    tag_service = TagService(user_info)
    tag_service.create_tag(tag=tag, color=color)
    return HttpResponse(status=200)


@require_http_methods(["PUT"])
@request_debug_log
@check_login
def ab_tag_rename(request, guid):
    token_service = TokenService()
    token, user_info, body = token_service.get_request_info(request)

    tag_old = body.get('old')
    tag_new = body.get('new')

    tag_service = TagService(user_info)
    tag_service.update_tag(tag=tag_old, new_tag=tag_new)
    return HttpResponse(status=200)


@require_http_methods(["DELETE"])
@request_debug_log
@check_login
def ab_tag(request, guid):
    token_service = TokenService()
    token, user_info, body = token_service.get_request_info(request)
    tags = body
    tag_service = TagService(user_info)
    tag_service.delete_tag(*list(tags))

    return HttpResponse(status=200)


@require_http_methods(["POST"])
@request_debug_log
@check_login
def ab_settings(request):
    return JsonResponse(
        {
            "max_peer_one_ab": 0
        }
    )


@request_debug_log
def ab_shared_profiles(request):
    return JsonResponse(
        {
            "total": 0,
            "data": [
                {
                    "guid": "1-1001-12",
                    "name": "研发部地址簿",
                    "owner": "alice",
                    "note": "",
                    "rule": 3
                },
                {
                    "guid": "1-1002-34",
                    "name": "IT支持共享",
                    "owner": "bob",
                    "note": "",
                    "rule": 2
                },
                {
                    "guid": "1-1003-56",
                    "name": "外包协作",
                    "owner": "carol",
                    "note": "",
                    "rule": 1
                }
            ]
        }
    )


@request_debug_log
def ab_peers(request):
    return JsonResponse(
        {
            'code': 1,
            'data': {
                'status': 1,
                'message': 'success'
            }
        }
    )
