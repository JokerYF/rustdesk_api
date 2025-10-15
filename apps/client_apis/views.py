import json
import logging

from django.contrib import auth
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.db.service import HeartBeatService, SystemInfoService, TokenService

logger = logging.getLogger(__name__)


@require_http_methods(["POST"])
def heartbeat(request: HttpRequest):
    # logger.debug(f'post_body: {request.body}')
    uuid = request.POST.get('uuid')
    client_id = request.POST.get('id')
    modified_at = request.POST.get('modified_at', timezone.now())
    ver = request.POST.get('ver')
    HeartBeatService().update(
        uuid=uuid,
        client_id=client_id,
        modified_at=modified_at,
        ver=ver,
    )
    return JsonResponse({'status': 'ok'})


@require_http_methods(["POST"])
def sysinfo(request: HttpRequest):
    # logger.debug(f'sysinfo post_body: {request.body}')
    request_body = json.loads(request.body.decode('utf-8'))
    uuid = request_body.get('uuid')

    SystemInfoService().update(
        uuid=uuid,
        client_id=request_body.get('id'),
        cpu=request_body.get('cpu'),
        hostname=request_body.get('hostname'),
        memory=request_body.get('memory'),
        os=request_body.get('os'),
        username=request_body.get('username'),
        version=request_body.get('version'),
    )
    return JsonResponse({'status': 'ok'})


@require_http_methods(["POST"])
def login(request: HttpRequest):
    username = request.POST.get('username')
    password = request.POST.get('password')
    uuid = request.POST.get('uuid')

    user = auth.authenticate(request, username=username, password=password)
    if not user:
        return JsonResponse({'error': '用户名或密码错误'})

    auth.login(request, user)
    token = TokenService().create_token(username, uuid)

    # 创建登录日志
    # login_log_service = LoginLogService()
    # login_log_service.create(**request_body)

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
    # logger.debug(f'logout post_body: {request.body}')
    uuid = request.POST.get('uuid')
    TokenService().delete_token_by_uuid(uuid)

    auth.logout(request)
    return JsonResponse({'code': 1})
