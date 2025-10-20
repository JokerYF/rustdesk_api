import json
import logging

from django.http import HttpRequest, JsonResponse

from apps.common.utils import get_uuid
from apps.db.service import TokenService, LoginClientService, SystemInfoService

logger = logging.getLogger('request_debug_log')


def check_login(func):
    """
    检查用户是否已登录的装饰器

    :param func: 被装饰的函数
    :return: 装饰后的函数
    """

    def wrapper(request: HttpRequest, *args, **kwargs):
        headers = request.headers
        if 'Authorization' not in headers:
            return JsonResponse({'error': '未登录'}, status=401)
        token_service = TokenService()
        token, user_info = token_service.get_user_token(request)
        uuid = token_service.get_cur_uuid_by_token(token)

        system_info = SystemInfoService()
        client_info = system_info.get_client_info_by_uuid(uuid)
        if not token_service.check_token(token, timeout=3600):
            # Server端记录登录信息
            LoginClientService().update_logout_status(
                uuid=uuid,
                username=user_info.username,
                client_id=client_info.client_id,
            )
            return JsonResponse({'error': '登录已过期'}, status=401)
        token_service.update_token(token)
        return func(request, *args, **kwargs)

    return wrapper


def request_debug_log(func):
    """
    记录请求日志的装饰器

    :param func: 被装饰的函数
    :return: 装饰后的函数
    """
    __uuid = get_uuid()

    def wrapper(request: HttpRequest, *args, **kwargs):
        request_log = {
            'method': request.method,
            'path': request.path,
            'headers': dict(request.headers),
        }
        if post := request.body:
            request_log['request_body'] = json.loads(post)
        elif post := request.POST:
            request_log['request_post_body'] = post.dict()

        logger.debug(f'request[{__uuid}]: {json.dumps(request_log)}')
        response = func(request, *args, **kwargs)
        response_log = json.dumps(
            {
                'status_code': response.status_code,
                'response_body': json.loads(response.content),
            }
        )
        logger.debug(f'response[{__uuid}]: {response_log}')
        return response

    return wrapper
