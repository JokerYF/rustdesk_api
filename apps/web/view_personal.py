from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods

from apps.client_apis.common import request_debug_log
from apps.db.service import (
    PersonalService, AliasService, PeerInfoService,
    HeartBeatService, ClientTagsService,
)


def is_default_personal(personal, user):
    """
    判断是否是默认地址簿

    :param personal: Personal对象
    :param user: User对象
    :return: 是否是默认地址簿
    :rtype: bool
    :notes:
    - 地址簿名称为"默认地址簿"
    - 或地址簿名称为"{用户名}_personal"
    """
    if personal.personal_name == '默认地址簿':
        return True
    if personal.personal_name == f'{user.username}_personal':
        return True
    return False


@request_debug_log
@require_http_methods(['POST'])
@login_required(login_url='web_login')
def create_personal(request: HttpRequest) -> JsonResponse:
    """
    创建地址簿

    :param request: POST，包含 personal_name, personal_type
    :return: {"ok": true, "data": {"guid": "xxx"}}
    """
    personal_name = (request.POST.get('personal_name') or '').strip()

    if not personal_name:
        return JsonResponse({'ok': False, 'err_msg': '地址簿名称不能为空'}, status=400)
    personal_type = 'public'

    personal_service = PersonalService()

    # 检查是否已存在同名地址簿
    if personal_service.personal_name_exists(request.user, personal_name):
        return JsonResponse({'ok': False, 'err_msg': '地址簿名称已存在'}, status=400)

    # 创建地址簿
    personal = personal_service.create_personal(
        personal_name=personal_name,
        create_user=request.user,
        personal_type=personal_type
    )

    return JsonResponse({'ok': True, 'data': {'guid': personal.guid}})


@request_debug_log
@require_http_methods(["POST"])
@login_required(login_url='web_login')
def delete_personal(request: HttpRequest) -> JsonResponse:
    """
    删除地址簿

    :param request: POST，包含 guid
    :return: {"ok": true}
    """
    guid = (request.POST.get('guid') or '').strip()

    if not guid:
        return JsonResponse({'ok': False, 'err_msg': '参数错误'}, status=400)

    personal_service = PersonalService()
    personal = personal_service.get_personal_by_user(guid, request.user)
    if not personal:
        return JsonResponse({'ok': False, 'err_msg': '地址簿不存在或无权限删除'}, status=404)

    # 检查是否是默认地址簿
    if is_default_personal(personal, request.user):
        return JsonResponse({'ok': False, 'err_msg': '默认地址簿不能删除'}, status=400)

    personal_service.delete_personal(guid)
    return JsonResponse({'ok': True})


@request_debug_log
@require_http_methods(["POST"])
@login_required(login_url='web_login')
def rename_personal(request: HttpRequest) -> JsonResponse:
    """
    重命名地址簿

    :param request: POST，包含 guid, new_name
    :return: {"ok": true}
    """
    guid = (request.POST.get('guid') or '').strip()
    new_name = (request.POST.get('new_name') or '').strip()

    if not guid or not new_name:
        return JsonResponse({'ok': False, 'err_msg': '参数错误'}, status=400)

    personal_service = PersonalService()
    personal = personal_service.get_personal_by_user(guid, request.user)
    if not personal:
        return JsonResponse({'ok': False, 'err_msg': '地址簿不存在或无权限修改'}, status=404)

    # 检查是否是默认地址簿
    if is_default_personal(personal, request.user):
        return JsonResponse({'ok': False, 'err_msg': '默认地址簿不能重命名'}, status=400)

    # 检查新名称是否已存在
    if personal_service.personal_name_exists(request.user, new_name, exclude_guid=guid):
        return JsonResponse({'ok': False, 'err_msg': '地址簿名称已存在'}, status=400)

    personal_service.rename_personal(guid, new_name)
    return JsonResponse({'ok': True})


@request_debug_log
@require_http_methods(["GET"])
@login_required(login_url='web_login')
def personal_detail(request: HttpRequest) -> JsonResponse:
    """
    获取地址簿详情（包含设备列表）

    :param request: GET，包含 guid
    :return: {"ok": true, "data": {...}}
    """
    guid = (request.GET.get('guid') or '').strip()

    if not guid:
        return JsonResponse({'ok': False, 'err_msg': '参数错误'}, status=400)

    personal_service = PersonalService()
    personal = personal_service.get_personal_by_user(guid, request.user)
    if not personal:
        return JsonResponse({'ok': False, 'err_msg': '地址簿不存在或无权限查看'}, status=404)

    peers = personal_service.get_peers_by_personal(guid=guid)

    # 获取所有peer的ID列表
    peer_ids = [peer_info.peer.peer_id for peer_info in peers]

    # 使用AliasService批量获取别名映射
    alias_map = AliasService().get_alias_map(guid=guid, peer_ids=peer_ids)

    heartbeat_service = HeartBeatService()
    client_tags_service = ClientTagsService()

    devices = []
    for peer_info in peers:
        peer = peer_info.peer
        # 检查在线状态
        is_online = heartbeat_service.is_online(peer.peer_id, uuid=peer.uuid)

        # 获取该设备在该地址簿中的标签
        tags = client_tags_service.get_tags_text_by_peer_in_personal(peer.peer_id, guid)

        devices.append({
            'peer_id': peer.peer_id,
            'alias': alias_map.get(peer.peer_id, ''),
            'tags': tags,
            'device_name': peer.device_name,
            'os': peer.os,
            'version': peer.version,
            'is_online': is_online,
            'created_at': peer.created_at.strftime('%Y-%m-%d %H:%M:%S') if peer.created_at else '',
        })

    data = {
        'guid': personal.guid,
        'personal_name': personal.personal_name,
        'display_name': '默认地址簿' if personal.personal_name == f'{request.user.username}_personal' else personal.personal_name,
        'personal_type': personal.personal_type,
        'created_at': personal.created_at.strftime('%Y-%m-%d %H:%M:%S') if personal.created_at else '',
        'device_count': len(devices),
        'devices': devices,
    }

    return JsonResponse({'ok': True, 'data': data})


@request_debug_log
@require_http_methods(['GET'])
@login_required(login_url='web_login')
def get_personal_list(request: HttpRequest) -> JsonResponse:
    """
    获取当前用户的所有地址簿列表（用于下拉选择）

    :param request: GET请求
    :return: {"ok": true, "data": [{"guid": "xxx", "name": "xxx", "display_name": "xxx"}, ...]}
    """

    personals = PersonalService().get_personals_by_creator(request.user, ordering=('personal_name',))

    data = []
    for personal in personals:
        if personal.personal_name == f'{request.user.username}_personal':
            display_name = '默认地址簿'
        else:
            display_name = personal.personal_name

        data.append({
            'guid': personal.guid,
            'name': personal.personal_name,
            'display_name': display_name,
        })

    return JsonResponse({'ok': True, 'data': data})


@request_debug_log
@require_http_methods(['POST'])
@login_required(login_url='web_login')
def add_device_to_personal(request: HttpRequest) -> JsonResponse:
    """
    添加设备到地址簿

    :param request: POST，包含 guid, peer_id, alias(可选)
    :return: {"ok": true}
    """
    guid = (request.POST.get('guid') or '').strip()
    peer_id = (request.POST.get('peer_id') or '').strip()
    alias_text = (request.POST.get('alias') or '').strip()

    if not guid or not peer_id:
        return JsonResponse({'ok': False, 'err_msg': '参数错误'}, status=400)

    personal_service = PersonalService()
    personal = personal_service.get_personal_by_user(guid, request.user)
    if not personal:
        return JsonResponse({'ok': False, 'err_msg': '地址簿不存在或无权限操作'}, status=404)

    peer = PeerInfoService().get_peer_info_by_peer_id(peer_id)
    if not peer:
        return JsonResponse({'ok': False, 'err_msg': '设备不存在'}, status=404)

    AliasService().set_alias(
        guid=guid,
        peer_id=peer_id,
        alias=alias_text
    )
    personal_service.add_peer_to_personal(
        guid=guid,
        peer_id=peer.peer_id,
    )

    return JsonResponse({'ok': True})


@request_debug_log
@require_http_methods(['POST'])
@login_required(login_url='web_login')
def remove_device_from_personal(request: HttpRequest) -> JsonResponse:
    """
    从地址簿移除设备

    :param request: POST，包含 guid, peer_id
    :return: {"ok": true}
    """
    guid = (request.POST.get('guid') or '').strip()
    peer_id = (request.POST.get('peer_id') or '').strip()

    if not guid or not peer_id:
        return JsonResponse({'ok': False, 'err_msg': '参数错误'}, status=400)

    personal_service = PersonalService()
    personal = personal_service.get_personal_by_user(guid, request.user)
    if not personal:
        return JsonResponse({'ok': False, 'err_msg': '地址簿不存在或无权限操作'}, status=404)

    personal_service.del_peer_to_personal(
        guid=guid,
        peer_id=peer_id,
        user=request.user
    )

    return JsonResponse({'ok': True})


@request_debug_log
@require_http_methods(['POST'])
@login_required(login_url='web_login')
def update_device_alias_in_personal(request: HttpRequest) -> JsonResponse:
    """
    在地址簿中更新设备别名

    :param request: POST，包含 guid, peer_id, alias
    :return: {"ok": true}
    """
    guid = (request.POST.get('guid') or '').strip()
    peer_id = (request.POST.get('peer_id') or '').strip()
    alias_text = (request.POST.get('alias') or '').strip()

    if not guid or not peer_id:
        return JsonResponse({'ok': False, 'err_msg': '参数错误'}, status=400)

    # 验证地址簿权限
    personal_service = PersonalService()
    personal = personal_service.get_personal_by_user(guid, request.user)
    if not personal:
        return JsonResponse({'ok': False, 'err_msg': '地址簿不存在或无权限操作'}, status=404)

    # 验证设备存在
    peer = PeerInfoService().get_peer_info_by_peer_id(peer_id)
    if not peer:
        return JsonResponse({'ok': False, 'err_msg': '设备不存在'}, status=404)

    # 如果别名为空，使用设备ID作为别名
    if not alias_text:
        alias_text = peer_id

    # 更新别名
    alias_service = AliasService()
    alias_obj = alias_service.get_alias_by_peer_and_personal(peer, personal)
    if not alias_obj:
        return JsonResponse({'ok': False, 'err_msg': '设备不在该地址簿中'}, status=404)

    alias_service.set_alias(guid=guid, peer_id=peer_id, alias=alias_text)

    return JsonResponse({'ok': True})


@request_debug_log
@require_http_methods(['POST'])
@login_required(login_url='web_login')
def update_device_tags_in_personal(request: HttpRequest) -> JsonResponse:
    """
    在地址簿中更新设备标签

    :param request: POST，包含 guid, peer_id, tags
    :return: {"ok": true}
    """
    guid = (request.POST.get('guid') or '').strip()
    peer_id = (request.POST.get('peer_id') or '').strip()
    tags_text = (request.POST.get('tags') or '').strip()

    if not guid or not peer_id:
        return JsonResponse({'ok': False, 'err_msg': '参数错误'}, status=400)

    # 验证地址簿权限
    personal_service = PersonalService()
    personal = personal_service.get_personal_by_user(guid, request.user)
    if not personal:
        return JsonResponse({'ok': False, 'err_msg': '地址簿不存在或无权限操作'}, status=404)

    # 验证设备存在
    peer = PeerInfoService().get_peer_info_by_peer_id(peer_id)
    if not peer:
        return JsonResponse({'ok': False, 'err_msg': '设备不存在'}, status=404)

    ClientTagsService().set_tags_for_peer_in_personal(
        user=request.user,
        peer_id=peer_id,
        guid=guid,
        tags_text=tags_text
    )

    return JsonResponse({'ok': True})
