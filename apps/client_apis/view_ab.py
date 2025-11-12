import logging

from django.http import HttpRequest, JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods

from apps.client_apis.common import request_debug_log, debug_request_None, check_login
from apps.db.models import Personal
from apps.db.service import TokenService, AliasService, TagService, PersonalService, SharePersonalService

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
@request_debug_log
@check_login
@debug_request_None
def ab(request: HttpRequest):
    # 好像在token失效后的残留页面会请求这个接口
    return None


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
def ab_tags(request, guid):
    token_service = TokenService(request=request)
    user_info = token_service.user_info
    tag_service = TagService(guid=guid, user=user_info)
    tags = tag_service.get_all_tags()
    data = [
        {
            'name': tag.tag,
            'color': int(tag.color),
        } for tag in tags
    ]
    return JsonResponse(data, safe=False, status=200)


@require_http_methods(["DELETE"])
@request_debug_log
@check_login
def ab_tag(request, guid):
    token_service = TokenService(request=request)
    body = token_service.request_body
    tags = body
    user_info = token_service.user_info
    tag_service = TagService(guid=guid, user=user_info)
    tag_service.delete_tag(*list(tags))

    return HttpResponse(status=200)


@require_http_methods(["POST", "PUT"])
@request_debug_log
@check_login
def ab_tag_add(request, guid):
    token_service = TokenService(request=request)
    user_info = token_service.user_info
    body = token_service.request_body
    tag = body.get('name')
    color = body.get('color')
    if request.method == "POST":
        tag_service = TagService(guid=guid, user=user_info)
        tag_service.create_tag(tag=tag, color=color)
    elif request.method == "PUT":
        tag_service = TagService(guid=guid, user=user_info)
        tag_service.update_tag(tag=tag, color=color)
    return HttpResponse(status=200)


@require_http_methods(["PUT"])
@request_debug_log
@check_login
def ab_tag_rename(request, guid):
    token_service = TokenService(request=request)
    body = token_service.request_body
    user_info = token_service.user_info

    tag_old = body.get('old')
    tag_new = body.get('new')

    tag_service = TagService(guid=guid, user=user_info)
    tag_service.update_tag(tag=tag_old, new_tag=tag_new)
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
    token_service = TokenService(request=request)
    user_info = token_service.user_info

    # 分享给自己的地址簿
    shared_personals = SharePersonalService(user_info).get_user_personals()

    # 自己创建的地址簿
    created_personals = user_info.user_personal.all()

    personal_data = []
    for personal in list(shared_personals) + list(created_personals):
        personal = personal if isinstance(personal, Personal) else personal.personal
        if personal.personal_type == 'private':
            continue
        personal_data.append(
            {
                "guid": personal.guid,
                "name": personal.personal_name,
            }
        )

    data = {
        "total": len(personal_data),
        "data": personal_data
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
    token_service = TokenService(request=request)
    user_info = token_service.user_info
    request_query = token_service.request_query
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
    peer_ids = [p.peer.peer_id for p in peers_qs]
    alias_map = AliasService().get_alias_map(guid=guid, peer_ids=peer_ids)
    tags_map = TagService(guid=guid, user=user_info).get_tags_map(peer_ids)

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
                "id": p.peer.peer_id,
                "username": p.peer.username,
                "hostname": p.peer.device_name,
                "alias": alias_map.get(p.peer.peer_id, ""),
                "platform": os_map[p.peer.os.split(' / ')[0]],
                "tags": tags_map.get(p.peer.peer_id, []),
            } for p in peers_qs
        ]
    }

    return JsonResponse(result)


@require_http_methods(["POST"])
@request_debug_log
@check_login
def ab_peer_add(request, guid):
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
    user_info = token_service.user_info
    body = token_service.request_body
    peer_id = body.get('id')

    if 'alias' in body.keys():
        AliasService().set_alias(
            guid=guid,
            peer_id=peer_id,
            alias=body.get('alias', '')
        )
    if 'tags' in body.keys():
        TagService(guid=guid, user=user_info).set_user_tag_by_peer_id(peer_id=peer_id, tags=body.get('tags', ''))
    return HttpResponse(status=200)


@require_http_methods(["DELETE"])
@request_debug_log
@check_login
def ab_peer_delete(request, guid):
    token_service = TokenService(request=request)
    user_info = token_service.user_info
    body = token_service.request_body
    PersonalService().del_peer_to_personal(
        guid=guid,
        peer_id=body,
        user=user_info
    )
    return HttpResponse(status=200)
