import json
import logging
import traceback

from django.contrib.auth.models import User
from django.http import HttpRequest, JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.client_apis.common import check_login, request_debug_log, debug_request_None
from apps.common.utils import get_local_time
from apps.db.models import SystemInfo
from apps.db.service import HeartBeatService, SystemInfoService, TokenService, UserService, \
    TagService, AuditConnService, PersonalService, AliasService, SharePersonalService

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
    return HttpResponse(status=200)


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

    try:
        user = User.objects.get(username=username)
        assert user.check_password(password)
    except User.DoesNotExist as e:
        logger.error(traceback.format_exc())
        return JsonResponse({'error': '用户名或密码错误'})

    token = token_service.create_token(username, uuid)

    # Server端记录登录信息
    # LoginClientService().update_login_status(
    #     uuid=SystemInfoService().get_client_info_by_uuid(uuid),
    #     username=user,
    #     client_id=body.get('id'),
    # )
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
    # LoginClientService().update_logout_status(
    #     uuid=uuid,
    #     username=user_info,
    #     client_id=body.get('id'),
    # )
    #
    # LogService().create_log(
    #     username=user_info,
    #     uuid=uuid,
    #     log_type='logout',
    #     log_message=f'用户 {user_info} 退出登录'
    # )
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
        token_service = TokenService(request=request)
        user_info = token_service.user_info
        body = token_service.request_body
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
    token_service = TokenService(request=request)
    user_info = token_service.user_info
    guid = user_info.user_personal.get(personal__personal_type='private').personal.guid
    return JsonResponse(
        {
            "guid": guid,
            "name": user_info.username,
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
    page = int(request.GET.get('current', 1))
    page_size = int(request.GET.get('pageSize', 10))

    token_service = TokenService(request=request)
    token = token_service.authorization
    user_info = token_service.user_info
    uuid = token_service.get_cur_uuid_by_token(token)

    client_list = SystemInfoService().get_list()
    data = []
    for client in client_list:
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
@debug_request_None  # 官方对于设备组有权限控制，目前无法控制，直接返回None，接口不报错即可
@check_login
def device_group_accessible(request):
    """
    admin获取当前服务端所有设备信息
    :param request:
    :return:
    """
    page = int(request.GET.get('current', 1))
    page_size = int(request.GET.get('pageSize', 10))

    token_service = TokenService(request=request)
    user_info = token_service.user_info

    client_list = SystemInfoService().get_list()
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
    type_ = body.get('type', 0)
    username = ''  # 发起者
    peer_id = ''  # 发起者peer id
    if peer := body.get('peer'):
        username = str(peer[-1]).lower()
        peer_id = peer[0]

    audit_service = AuditConnService()
    audit_service.log(
        conn_id=conn_id,
        action=action,
        controlled_uuid=controlled_uuid,
        source_ip=ip,
        session_id=session_id,
        controller_peer_id=peer_id,
        type_=type_,
        username=username
    )

    return HttpResponse(status=200)


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

    return HttpResponse(status=200)


@require_http_methods(["POST"])
@request_debug_log
@check_login
def ab_tags(request, guid):
    tag_service = TagService(guid=guid)
    tags = tag_service.get_all_tags()
    data = [
        {
            'name': tag.tag,
            'color': int(tag.color),
        } for tag in tags
    ]
    return JsonResponse(data, safe=False, status=200)


@require_http_methods(["POST"])
@request_debug_log
@check_login
def ab_tag_add(request, guid):
    token_service = TokenService(request=request)
    body = token_service.request_body
    tag = body.get('name')
    color = body.get('color')

    tag_service = TagService(guid=guid)
    tag_service.create_tag(tag=tag, color=color)
    return HttpResponse(status=200)


@require_http_methods(["PUT"])
@request_debug_log
@check_login
def ab_tag_rename(request, guid):
    token_service = TokenService(request=request)
    body = token_service.request_body

    tag_old = body.get('old')
    tag_new = body.get('new')

    tag_service = TagService(guid=guid)
    tag_service.update_tag(tag=tag_old, new_tag=tag_new)
    return HttpResponse(status=200)


@require_http_methods(["DELETE"])
@request_debug_log
@check_login
def ab_tag(request, guid):
    token_service = TokenService(request=request)
    body = token_service.request_body
    tags = body
    tag_service = TagService(guid=guid)
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


@require_http_methods(["POST"])
@request_debug_log
@check_login
def ab_shared_profiles(request):
    # {
    #     "total": 0,
    #     "data": [
    #         {
    #             "guid": "1-1001-12",
    #             "name": "研发部地址簿",
    #         }
    #     ]
    # }
    token_service = TokenService(request=request)
    user_info = token_service.user_info

    # 用户对应的地址簿
    personals = SharePersonalService(user_info).get_user_personals()

    data = {
        "total": len(personals),
        "data": [
            {
                "guid": personal.guid,
                "name": personal.personal_name,
            } for personal in personals if personal.personal.personal_type != 'private'
        ]
    }

    return JsonResponse(data)


@require_http_methods(["POST"])
@request_debug_log
@check_login
def ab_peers(request):
    """
    返回用户添加到地址簿的设备列表
    :param request:
    :return:
    """
    # result = {
    #     "total": 1,
    #     "data": [
    #         {
    #             # "row_id": 12,
    #             "id": "488591401",
    #             "username": "pcuser",
    #             # "password": "",
    #             "hostname": "HOST-01",
    #             "alias": "办公PC",
    #             "platform": "Windows",
    #             "tags": ["重要", "外网"],
    #             # "hash": "",
    #             # "user_id": 3,
    #             # "forceAlwaysRelay": False,
    #             # "rdpPort": "",
    #             # "rdpUsername": "",
    #             # "online": True,
    #             # "loginName": "pcuser",
    #             # "sameServer": True,
    #             # "collection_id": 5
    #         }
    #     ],
    #     "licensed_devices": 99999
    # }

    token_service = TokenService(request=request)
    request_query = token_service.request_query
    page = int(request_query.get('current', 1))
    page_size = int(request_query.get('pageSize', 10))
    guid = request_query.get('ab')

    personal_service = PersonalService()
    try:
        # 结合 select_related 一次性拉取 `peer`，避免 N+1
        peers_qs = personal_service.get_personal(guid).personal_peer.select_related('peer').all()
    except Exception:
        logger.error(f'[ab_peers] get personal error: {guid}')
        return JsonResponse(
            {
                "total": 0,
                "data": []
            }
        )

    # 预取 alias 和 tags，使用批量映射减少查询
    peer_ids = [p.peer.client_id for p in peers_qs]
    alias_map = AliasService().get_alias_map(guid=guid, peer_ids=peer_ids)
    tags_map = TagService(guid=guid).get_tags_map(peer_ids)

    os_map = {
        'windows': 'Windows',
        'linux': 'Linux',
        'macos': 'Mac OS',
        'android': 'Android',
    }

    result = {
        "total": peers_qs.count(),
        "data": [
            {
                "id": p.peer.client_id,
                "username": p.peer.username,
                "hostname": p.peer.device_name,
                "alias": alias_map.get(p.peer.client_id, ""),
                "platform": os_map[p.peer.os.split(' / ')[0]],
                "tags": tags_map.get(p.peer.client_id, []),
            } for p in peers_qs
        ]
    }

    return JsonResponse(result)


@require_http_methods(["POST"])
@request_debug_log
@check_login
def ab_peer_add(request, guid):
    # {
    #     "id": "163052894",
    #     "username": "lenovo",
    #     "hostname": "lenovodemac-mini",
    #     "platform": "Mac OS",
    #     "alias": "",
    #     "tags": [],
    #     "forceAlwaysRelay": "false",
    #     "rdpPort": "",
    #     "rdpUsername": "",
    #     "loginName": "admin",
    #     "device_group_name": "",
    #     "same_server": null
    # }
    token_service = TokenService(request=request)
    body = token_service.request_body
    try:
        PersonalService().add_peer_to_personal(
            guid=guid,
            peer_id=body.get('id'),
        )
        return HttpResponse(status=200)
    except:
        return JsonResponse(
            {'error': 'Add peer to personal failed'}
        )


@require_http_methods(["PUT"])
@request_debug_log
@check_login
def ab_peer_update(request, guid):
    token_service = TokenService(request=request)
    body = token_service.request_body
    peer_id = body.get('id')

    if 'alias' in body.keys():
        AliasService().set_alias(
            guid=guid,
            peer_id=peer_id,
            alias=body.get('alias', '')
        )
    if 'tags' in body.keys():
        TagService(guid=guid).set_tag_by_peer_id(
            peer_id=peer_id,
            tags=body.get('tags', ''),
        )
    return HttpResponse(status=200)


@require_http_methods(["DELETE"])
@request_debug_log
@check_login
def ab_peer_delete(request, guid):
    token_service = TokenService(request=request)
    body = token_service.request_body
    PersonalService().del_peer_to_personal(
        guid=guid,
        peer_id=body,
    )
    return HttpResponse(status=200)
