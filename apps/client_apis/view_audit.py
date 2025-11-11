import json

from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_http_methods

from apps.client_apis.common import request_debug_log
from apps.db.service import AuditConnService


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
