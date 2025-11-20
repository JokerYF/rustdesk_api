import json
import logging
import traceback

from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_http_methods

from apps.client_apis.common import request_debug_log
from apps.db.service import AuditConnService, TokenService, AuditFileLogService, UserService

logger = logging.getLogger(__name__)


@request_debug_log
@require_http_methods(["POST"])
def audit_conn(request: HttpRequest):
    """
    连接日志
    :param request:
    :return:
    """
    token_service = TokenService(request=request)
    body = token_service.request_body
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


@request_debug_log
@require_http_methods(["POST"])
def audit_file(request):
    """
    文件日志
    :param request:
    :return:
    """
    token_service = TokenService(request=request)
    body = token_service.request_body
    target_peer_id = body.get('id')
    file_info = json.loads(body.get('info'))
    is_file = body.get('is_file')
    file_path = body.get('path')
    source_peer_id = body.get('peer_id')
    type_ = body.get('type')  # 0:下载 1:上传
    uuid = body.get('uuid')

    try:
        user_id = UserService().get_user_by_name(file_info.get('name').lower()).id
    except Exception:
        logger.error(traceback.format_exc())
        user_id = ''

    file_service = AuditFileLogService()
    file_service.log(
        source_id=source_peer_id,
        target_id=target_peer_id,
        target_uuid=uuid,
        target_ip=file_info.get('ip'),
        operation_type=type_,
        is_file=is_file,
        remote_path=file_path,
        file_info=str(file_info.get('files')),
        user_id=user_id,
        file_num=file_info.get('num'),
    )

    return HttpResponse(status=200)
