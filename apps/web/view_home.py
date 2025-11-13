from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q, Exists, OuterRef, F, Subquery
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone

from apps.client_apis.common import request_debug_log
from apps.db.models import PeerInfo, HeartBeat, Alias, ClientTags, Personal


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


@request_debug_log
@login_required(login_url='web_login')
def nav_content(request: HttpRequest) -> HttpResponse:
    """
    返回侧边导航对应的局部模板内容（通过 GET 参数 key）

    :param request: Http 请求对象，需包含 GET 参数 key（如 nav-1/nav-2/nav-3）
    :type request: HttpRequest
    :return: 渲染后的 HTML 片段
    :rtype: HttpResponse
    :notes:
    - 仅支持预设键名，未知键名将返回简单的占位内容
    """
    key = request.GET.get('key', '').strip()
    key_to_template = {
        'nav-1': 'nav/nav-1.html',
        'nav-2': 'nav/nav-2.html',
        'nav-3': 'nav/nav-3.html',
        'nav-4': 'nav/nav-4.html',
    }
    template_name = key_to_template.get(key)
    if not template_name:
        # 未知 key，返回占位内容而非 404，便于前端保持一致渲染
        return HttpResponse('<p class="content-empty">未匹配到内容</p>')
    # 根据不同导航项提供对应数据
    context = {}
    if key == 'nav-1':  # 首页
        # 分页参数
        try:
            page = int(request.GET.get('page', 1))
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = int(request.GET.get('page_size', 20))
        except (TypeError, ValueError):
            page_size = 20

        user_count = User.objects.count()
        queryset = PeerInfo.objects.order_by('-created_at')
        device_count = queryset.count()
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        # 当前页设备列表
        devices = page_obj.object_list
        context.update({
            'user_count': user_count,
            'device_count': device_count,
            'devices': devices,
            'paginator': paginator,
            'page_obj': page_obj,
            'page_size': page_size,
        })
    elif key == 'nav-2':  # 设备管理
        """
        设备管理（nav-2）上下文构建

        :query page: 页码（默认 1）
        :query page_size: 每页大小（默认 20）
        :query q: 关键词，匹配设备ID/设备名（可空）
        :query os: 操作系统筛选（可空；模糊匹配）
        :query status: 在线状态（online/offline，可空）
        :returns: 注入模板的设备分页、筛选上下文
        :rtype: HttpResponse
        """
        # 基本分页参数
        try:
            page = int(request.GET.get('page', 1))
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = int(request.GET.get('page_size', 20))
        except (TypeError, ValueError):
            page_size = 20

        # 筛选参数
        q = (request.GET.get('q') or '').strip()
        os_param = (request.GET.get('os') or '').strip()
        status = (request.GET.get('status') or '').strip().lower()

        # 在线判定：心跳表 5 分钟内有记录视为在线
        online_threshold = timezone.now() - timedelta(minutes=5)
        recent_hb = HeartBeat.objects.filter(
            Q(peer_id=OuterRef('peer_id')) | Q(uuid=OuterRef('uuid')),
            modified_at__gte=online_threshold
        ).values('pk')[:1]

        base_qs = PeerInfo.objects.all().annotate(
            is_online=Exists(recent_hb),
            owner_username=F('username'),
            # 别名：取任意一个别名（如存在）
            alias=Subquery(
                Alias.objects.filter(
                    peer_id=OuterRef('peer_id')
                ).values('alias')[:1]
            ),
            # 标签：取当前登录用户下的一个标签（如存在）
            tags=Subquery(
                ClientTags.objects.filter(
                    peer_id=OuterRef('peer_id'),
                    user=request.user
                ).values('tags')[:1]
            )
        ).order_by('-created_at')

        if q:
            base_qs = base_qs.filter(Q(peer_id__icontains=q) | Q(device_name__icontains=q))
        if os_param:
            base_qs = base_qs.filter(os__icontains=os_param)
        if status in ('online', 'offline'):
            want_online = (status == 'online')
            base_qs = base_qs.filter(is_online=want_online)

        paginator = Paginator(base_qs, page_size)
        page_obj = paginator.get_page(page)
        devices = page_obj.object_list

        context.update({
            'devices': devices,
            'paginator': paginator,
            'page_obj': page_obj,
            'page_size': page_size,
            # 透传筛选回显
            'q': q,
            'os': os_param,
            'status': status,
        })
    elif key == 'nav-3':  # 用户管理
        # 分页参数
        try:
            page = int(request.GET.get('page', 1))
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = int(request.GET.get('page_size', 20))
        except (TypeError, ValueError):
            page_size = 20
        # 搜索参数
        q = (request.GET.get('q') or '').strip()
        user_qs = User.objects.all().order_by('-date_joined')
        if q:
            user_qs = user_qs.filter(
                Q(username__icontains=q) |
                Q(email__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q)
            )
        paginator = Paginator(user_qs, page_size)
        page_obj = paginator.get_page(page)
        users = page_obj.object_list
        context.update({
            'users': users,
            'paginator': paginator,
            'page_obj': page_obj,
            'page_size': page_size,
            'q': q,
        })
    elif key == 'nav-4':  # 地址簿
        # 分页参数
        try:
            page = int(request.GET.get('page', 1))
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = int(request.GET.get('page_size', 20))
        except (TypeError, ValueError):
            page_size = 20
        # 搜索参数
        q = (request.GET.get('q') or '').strip()
        personal_type = (request.GET.get('type') or '').strip()

        # 查询当前用户的地址簿（包括自己创建的和被分享的）
        personal_qs = Personal.objects.filter(create_user=request.user).order_by('-created_at')

        # 搜索过滤（使用guid进行搜索）
        if q:
            personal_qs = personal_qs.filter(guid__icontains=q)
        if personal_type in ('public', 'private'):
            personal_qs = personal_qs.filter(personal_type=personal_type)

        paginator = Paginator(personal_qs, page_size)
        page_obj = paginator.get_page(page)
        personals = list(page_obj.object_list)

        # 为每个地址簿统计设备数量并标记是否为默认地址簿
        for personal in personals:
            device_count = Alias.objects.filter(guid=personal).count()
            personal.device_count = device_count
            personal.is_default = is_default_personal(personal, request.user)
            # 设置显示名称：如果是 {用户名}_personal 格式，显示为"默认地址簿"
            if personal.personal_name == f'{request.user.username}_personal':
                personal.display_name = '默认地址簿'
            else:
                personal.display_name = personal.personal_name

        context.update({
            'personals': personals,
            'paginator': paginator,
            'page_obj': page_obj,
            'page_size': page_size,
            'q': q,
            'personal_type': personal_type,
        })
    return render(request, template_name, context=context)


@request_debug_log
@login_required(login_url='web_login')
def rename_alias(request: HttpRequest) -> JsonResponse:
    """
    重命名设备别名（创建或更新 Alias）

    :param request: Http 请求对象，POST 参数包含 peer_id, alias
    :type request: HttpRequest
    :return: JSON 响应，形如 {"ok": true}
    :rtype: JsonResponse
    :notes:
    - 别名基于用户的“默认地址簿”（如不存在则自动创建，私有）
    - 针对 (peer_id, 默认地址簿) 维度进行 upsert
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'err_msg': 'Method not allowed'}, status=405)
    peer_id = (request.POST.get('peer_id') or '').strip()
    alias_text = (request.POST.get('alias') or '').strip()
    if not peer_id or not alias_text:
        return JsonResponse({'ok': False, 'err_msg': '参数错误'}, status=400)
    peer = PeerInfo.objects.filter(peer_id=peer_id).first()
    if not peer:
        return JsonResponse({'ok': False, 'err_msg': '设备不存在'}, status=404)
    # 获取或创建默认地址簿（私有）
    personal, _ = Personal.objects.get_or_create(
        create_user=request.user,
        personal_type='private',
        personal_name='默认地址簿',
        defaults={}
    )
    Alias.objects.update_or_create(
        peer_id=peer,
        guid=personal,
        defaults={'alias': alias_text}
    )
    return JsonResponse({'ok': True})


@request_debug_log
@login_required(login_url='web_login')
def device_detail(request: HttpRequest) -> JsonResponse:
    """
    获取设备详情（peer 维度）

    :param request: Http 请求对象，GET 参数包含 peer_id
    :type request: HttpRequest
    :return: JSON 响应，包含 peer_id/username/hostname/alias/platform/tags
    :rtype: JsonResponse
    """
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'err_msg': 'Method not allowed'}, status=405)
    peer_id = (request.GET.get('peer_id') or '').strip()
    if not peer_id:
        return JsonResponse({'ok': False, 'err_msg': '参数错误'}, status=400)
    peer = PeerInfo.objects.filter(peer_id=peer_id).first()
    if not peer:
        return JsonResponse({'ok': False, 'err_msg': '设备不存在'}, status=404)
    # 默认地址簿下的 alias（若无则回退任意一个 alias）
    default_personal = Personal.objects.filter(
        create_user=request.user,
        personal_type='private',
        personal_name='默认地址簿'
    ).first()
    alias_qs = Alias.objects.filter(peer_id=peer)
    if default_personal:
        prefer = alias_qs.filter(guid=default_personal).values_list('alias', flat=True).first()
        alias_text = prefer if prefer is not None else alias_qs.values_list('alias', flat=True).first()
    else:
        alias_text = alias_qs.values_list('alias', flat=True).first()
    alias_text = alias_text or ''
    # 当前用户下的标签（可能多条）
    tag_list = list(ClientTags.objects.filter(user=request.user, peer_id=peer_id).values_list('tags', flat=True))
    # 构造响应
    data = {
        'peer_id': peer.peer_id,
        'username': peer.username,
        'hostname': peer.device_name,
        'alias': alias_text,
        'platform': peer.os,
        'tags': tag_list,
    }
    return JsonResponse({'ok': True, 'data': data})


@request_debug_log
@login_required(login_url='web_login')
def update_device(request: HttpRequest) -> JsonResponse:
    """
    内联更新设备信息（别名与标签）

    :param request: Http 请求对象，POST 参数：
        - peer_id: 设备ID（必填）
        - alias: 设备别名（可选，空则忽略）
        - tags: 设备标签（可选，逗号分隔；空字符串表示清空）
    :type request: HttpRequest
    :return: JSON 响应，形如 {"ok": true}
    :rtype: JsonResponse
    :notes:
    - 别名写入当前用户的“默认地址簿”（不存在则创建）
    - 标签写入 ClientTags（当前用户 + 默认地址簿 guid 作用域）
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'err_msg': 'Method not allowed'}, status=405)
    peer_id = (request.POST.get('peer_id') or '').strip()
    if not peer_id:
        return JsonResponse({'ok': False, 'err_msg': '参数错误'}, status=400)
    peer = PeerInfo.objects.filter(peer_id=peer_id).first()
    if not peer:
        return JsonResponse({'ok': False, 'err_msg': '设备不存在'}, status=404)

    alias_text = request.POST.get('alias')
    tags_str = request.POST.get('tags')

    # 获取/创建默认地址簿（私有）
    personal, _ = Personal.objects.get_or_create(
        create_user=request.user,
        personal_type='private',
        personal_name='默认地址簿',
        defaults={}
    )

    # 更新别名（当 alias 参数存在时）
    if alias_text is not None:
        alias_text = alias_text.strip()
        if alias_text:
            Alias.objects.update_or_create(
                peer_id=peer,
                guid=personal,
                defaults={'alias': alias_text}
            )
        else:
            # 空字符串表示清除当前作用域下别名
            Alias.objects.filter(peer_id=peer, guid=personal).delete()

    # 更新标签（当 tags 参数存在时）
    if tags_str is not None:
        # 归一化标签：逗号分隔，去空白、去重，保持顺序
        parts = [p.strip() for p in tags_str.split(',')] if tags_str is not None else []
        parts = [p for p in parts if p]
        seen = set()
        uniq = []
        for p in parts:
            if p not in seen:
                seen.add(p)
                uniq.append(p)
        joined = ', '.join(uniq)
        if joined:
            ClientTags.objects.update_or_create(
                user=request.user,
                peer_id=peer_id,
                guid=personal.guid,
                defaults={'tags': joined}
            )
        else:
            # 空表示清空标签
            ClientTags.objects.filter(user=request.user, peer_id=peer_id, guid=personal.guid).delete()

    return JsonResponse({'ok': True})


@request_debug_log
@login_required(login_url='web_login')
def device_statuses(request: HttpRequest) -> JsonResponse:
    """
    批量获取设备在线状态（仅查询，不修改会话）

    :param request: Http 请求对象，GET 参数：
        - ids: 逗号分隔的设备ID列表，如 "id1,id2,id3"
    :type request: HttpRequest
    :return: JSON 响应，形如 {"ok": true, "data": {"<peer_id>": {"is_online": true/false}}}
    :rtype: JsonResponse
    :notes:
        - 前端应在请求头携带 ``X-Session-No-Renew: 1``，以避免该轮询请求“续命”会话
        - 仅执行只读查询，不做任何写操作
    """
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'err_msg': 'Method not allowed'}, status=405)
    raw_ids = (request.GET.get('ids') or '').strip()
    if not raw_ids:
        return JsonResponse({'ok': True, 'data': {}})
    # 归一化与限流（防止一次性过大）
    peer_ids = [p.strip() for p in raw_ids.split(',') if p.strip()]
    if not peer_ids:
        return JsonResponse({'ok': True, 'data': {}})
    peer_ids = peer_ids[:500]
    # 60s 内有心跳视为在线
    online_threshold = timezone.now() - timedelta(seconds=60)
    online_qs = HeartBeat.objects.filter(
        peer_id__in=peer_ids,
        modified_at__gte=online_threshold
    ).values_list('peer_id', flat=True).distinct()
    online_set = set(online_qs)
    data = {pid: {'is_online': (pid in online_set)} for pid in peer_ids}
    return JsonResponse({'ok': True, 'data': data})


@request_debug_log
@login_required(login_url='web_login')
def update_user(request: HttpRequest) -> JsonResponse:
    """
    更新用户基础信息（仅限管理员）

    :param request: POST，包含 username, full_name(可选), email(可选), is_staff(可选: '1'/'0')
    :return: {"ok": true}
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'err_msg': 'Method not allowed'}, status=405)
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
    if full_name != '':
        # 仅使用 first_name 存储展示用姓名
        user.first_name = full_name
        user.last_name = ''
    if email != '':
        user.email = email
    if is_staff_raw is not None:
        user.is_staff = (str(is_staff_raw).strip() == '1')
    user.save(update_fields=['first_name', 'last_name', 'email', 'is_staff'])
    return JsonResponse({'ok': True})


@request_debug_log
@login_required(login_url='web_login')
def reset_user_password(request: HttpRequest) -> JsonResponse:
    """
    重置用户密码（仅限管理员）

    :param request: POST，包含 username, password1, password2
    :return: {"ok": true}
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'err_msg': 'Method not allowed'}, status=405)
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
@login_required(login_url='web_login')
def create_personal(request: HttpRequest) -> JsonResponse:
    """
    创建地址簿

    :param request: POST，包含 personal_name, personal_type
    :return: {"ok": true, "data": {"guid": "xxx"}}
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'err_msg': 'Method not allowed'}, status=405)
    personal_name = (request.POST.get('personal_name') or '').strip()
    # personal_type = (request.POST.get('personal_type') or '').strip()

    if not personal_name:
        return JsonResponse({'ok': False, 'err_msg': '地址簿名称不能为空'}, status=400)
    # if personal_type not in ('public', 'private'):
    #     personal_type = 'private'
    personal_type = 'public'

    # 检查是否已存在同名地址簿
    existing = Personal.objects.filter(
        create_user=request.user,
        personal_name=personal_name
    ).first()
    if existing:
        return JsonResponse({'ok': False, 'err_msg': '地址簿名称已存在'}, status=400)

    # 创建地址簿
    personal = Personal.objects.create(
        personal_name=personal_name,
        create_user=request.user,
        personal_type=personal_type
    )

    return JsonResponse({'ok': True, 'data': {'guid': personal.guid}})


@request_debug_log
@login_required(login_url='web_login')
def delete_personal(request: HttpRequest) -> JsonResponse:
    """
    删除地址簿

    :param request: POST，包含 guid
    :return: {"ok": true}
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'err_msg': 'Method not allowed'}, status=405)
    guid = (request.POST.get('guid') or '').strip()

    if not guid:
        return JsonResponse({'ok': False, 'err_msg': '参数错误'}, status=400)

    personal = Personal.objects.filter(guid=guid, create_user=request.user).first()
    if not personal:
        return JsonResponse({'ok': False, 'err_msg': '地址簿不存在或无权限删除'}, status=404)

    # 检查是否是默认地址簿
    if is_default_personal(personal, request.user):
        return JsonResponse({'ok': False, 'err_msg': '默认地址簿不能删除'}, status=400)

    personal.delete()
    return JsonResponse({'ok': True})


@request_debug_log
@login_required(login_url='web_login')
def rename_personal(request: HttpRequest) -> JsonResponse:
    """
    重命名地址簿

    :param request: POST，包含 guid, new_name
    :return: {"ok": true}
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'err_msg': 'Method not allowed'}, status=405)
    guid = (request.POST.get('guid') or '').strip()
    new_name = (request.POST.get('new_name') or '').strip()

    if not guid or not new_name:
        return JsonResponse({'ok': False, 'err_msg': '参数错误'}, status=400)

    personal = Personal.objects.filter(guid=guid, create_user=request.user).first()
    if not personal:
        return JsonResponse({'ok': False, 'err_msg': '地址簿不存在或无权限修改'}, status=404)

    # 检查是否是默认地址簿
    if is_default_personal(personal, request.user):
        return JsonResponse({'ok': False, 'err_msg': '默认地址簿不能重命名'}, status=400)

    # 检查新名称是否已存在
    existing = Personal.objects.filter(
        create_user=request.user,
        personal_name=new_name
    ).exclude(guid=guid).first()
    if existing:
        return JsonResponse({'ok': False, 'err_msg': '地址簿名称已存在'}, status=400)

    personal.personal_name = new_name
    personal.save(update_fields=['personal_name'])
    return JsonResponse({'ok': True})


@request_debug_log
@login_required(login_url='web_login')
def personal_detail(request: HttpRequest) -> JsonResponse:
    """
    获取地址簿详情（包含设备列表）

    :param request: GET，包含 guid
    :return: {"ok": true, "data": {...}}
    """
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'err_msg': 'Method not allowed'}, status=405)
    guid = (request.GET.get('guid') or '').strip()

    if not guid:
        return JsonResponse({'ok': False, 'err_msg': '参数错误'}, status=400)

    personal = Personal.objects.filter(guid=guid, create_user=request.user).first()
    if not personal:
        return JsonResponse({'ok': False, 'err_msg': '地址簿不存在或无权限查看'}, status=404)

    # 获取地址簿中的设备（通过Alias表关联）
    aliases = Alias.objects.filter(guid=personal).select_related('peer_id').order_by('-created_at')

    # 在线判定：心跳表 5 分钟内有记录视为在线
    online_threshold = timezone.now() - timedelta(minutes=5)

    devices = []
    for alias in aliases:
        peer = alias.peer_id
        # 检查在线状态
        is_online = HeartBeat.objects.filter(
            Q(peer_id=peer.peer_id) | Q(uuid=peer.uuid),
            modified_at__gte=online_threshold
        ).exists()

        # 获取该设备在该地址簿中的标签
        client_tags = ClientTags.objects.filter(peer_id=peer.peer_id, guid=guid).first()
        tags = client_tags.tags if client_tags else ''

        devices.append({
            'peer_id': peer.peer_id,
            'alias': alias.alias,
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
@login_required(login_url='web_login')
def get_personal_list(request: HttpRequest) -> JsonResponse:
    """
    获取当前用户的所有地址簿列表（用于下拉选择）

    :param request: GET请求
    :return: {"ok": true, "data": [{"guid": "xxx", "name": "xxx", "display_name": "xxx"}, ...]}
    """
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'err_msg': 'Method not allowed'}, status=405)

    # 获取当前用户的所有地址簿
    personals = Personal.objects.filter(create_user=request.user).order_by('personal_name')

    data = []
    for personal in personals:
        # 设置显示名称：如果是 {用户名}_personal 格式，显示为"默认地址簿"
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
@login_required(login_url='web_login')
def add_device_to_personal(request: HttpRequest) -> JsonResponse:
    """
    添加设备到地址簿

    :param request: POST，包含 guid, peer_id, alias(可选)
    :return: {"ok": true}
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'err_msg': 'Method not allowed'}, status=405)
    guid = (request.POST.get('guid') or '').strip()
    peer_id = (request.POST.get('peer_id') or '').strip()
    alias_text = (request.POST.get('alias') or '').strip()

    if not guid or not peer_id:
        return JsonResponse({'ok': False, 'err_msg': '参数错误'}, status=400)

    personal = Personal.objects.filter(guid=guid, create_user=request.user).first()
    if not personal:
        return JsonResponse({'ok': False, 'err_msg': '地址簿不存在或无权限操作'}, status=404)

    peer = PeerInfo.objects.filter(peer_id=peer_id).first()
    if not peer:
        return JsonResponse({'ok': False, 'err_msg': '设备不存在'}, status=404)

    # 使用设备ID作为默认别名
    if not alias_text:
        alias_text = peer_id

    # 添加或更新别名（如果已存在则更新）
    Alias.objects.update_or_create(
        peer_id=peer,
        guid=personal,
        defaults={'alias': alias_text}
    )

    return JsonResponse({'ok': True})


@request_debug_log
@login_required(login_url='web_login')
def remove_device_from_personal(request: HttpRequest) -> JsonResponse:
    """
    从地址簿移除设备

    :param request: POST，包含 guid, peer_id
    :return: {"ok": true}
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'err_msg': 'Method not allowed'}, status=405)
    guid = (request.POST.get('guid') or '').strip()
    peer_id = (request.POST.get('peer_id') or '').strip()

    if not guid or not peer_id:
        return JsonResponse({'ok': False, 'err_msg': '参数错误'}, status=400)

    personal = Personal.objects.filter(guid=guid, create_user=request.user).first()
    if not personal:
        return JsonResponse({'ok': False, 'err_msg': '地址簿不存在或无权限操作'}, status=404)

    # 删除别名记录
    deleted_count = Alias.objects.filter(
        peer_id__peer_id=peer_id,
        guid=personal
    ).delete()[0]

    if deleted_count == 0:
        return JsonResponse({'ok': False, 'err_msg': '设备不在该地址簿中'}, status=404)

    return JsonResponse({'ok': True})


@request_debug_log
@login_required(login_url='web_login')
def update_device_alias_in_personal(request: HttpRequest) -> JsonResponse:
    """
    在地址簿中更新设备别名

    :param request: POST，包含 guid, peer_id, alias
    :return: {"ok": true}
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'err_msg': 'Method not allowed'}, status=405)
    guid = (request.POST.get('guid') or '').strip()
    peer_id = (request.POST.get('peer_id') or '').strip()
    alias_text = (request.POST.get('alias') or '').strip()

    if not guid or not peer_id:
        return JsonResponse({'ok': False, 'err_msg': '参数错误'}, status=400)

    # 验证地址簿权限
    personal = Personal.objects.filter(guid=guid, create_user=request.user).first()
    if not personal:
        return JsonResponse({'ok': False, 'err_msg': '地址簿不存在或无权限操作'}, status=404)

    # 验证设备存在
    peer = PeerInfo.objects.filter(peer_id=peer_id).first()
    if not peer:
        return JsonResponse({'ok': False, 'err_msg': '设备不存在'}, status=404)

    # 如果别名为空，使用设备ID作为别名
    if not alias_text:
        alias_text = peer_id

    # 更新别名
    alias_obj = Alias.objects.filter(peer_id=peer, guid=personal).first()
    if not alias_obj:
        return JsonResponse({'ok': False, 'err_msg': '设备不在该地址簿中'}, status=404)

    alias_obj.alias = alias_text
    alias_obj.save(update_fields=['alias'])

    return JsonResponse({'ok': True})


@request_debug_log
@login_required(login_url='web_login')
def update_device_tags_in_personal(request: HttpRequest) -> JsonResponse:
    """
    在地址簿中更新设备标签

    :param request: POST，包含 guid, peer_id, tags
    :return: {"ok": true}
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'err_msg': 'Method not allowed'}, status=405)
    guid = (request.POST.get('guid') or '').strip()
    peer_id = (request.POST.get('peer_id') or '').strip()
    tags_text = (request.POST.get('tags') or '').strip()

    if not guid or not peer_id:
        return JsonResponse({'ok': False, 'err_msg': '参数错误'}, status=400)

    # 验证地址簿权限
    personal = Personal.objects.filter(guid=guid, create_user=request.user).first()
    if not personal:
        return JsonResponse({'ok': False, 'err_msg': '地址簿不存在或无权限操作'}, status=404)

    # 验证设备存在
    peer = PeerInfo.objects.filter(peer_id=peer_id).first()
    if not peer:
        return JsonResponse({'ok': False, 'err_msg': '设备不存在'}, status=404)

    # 更新标签（在ClientTags表中）
    # 先删除该设备在该地址簿的所有标签
    ClientTags.objects.filter(peer_id=peer_id, guid=guid).delete()

    # 如果有新标签，则添加
    if tags_text:
        ClientTags.objects.create(
            user=request.user,
            peer_id=peer_id,
            tags=tags_text,
            guid=guid
        )

    return JsonResponse({'ok': True})
