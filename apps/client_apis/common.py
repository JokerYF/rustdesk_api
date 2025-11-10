import json
import logging
import time
import traceback
from functools import wraps

from django.http import HttpRequest, JsonResponse, HttpResponse

from apps.db.service import TokenService, PeerInfoService
from common.utils import get_randem_md5

logger = logging.getLogger('request_debug_log')


def check_login(func):
    """
    检查用户是否已登录的装饰器

    :param func: 被装饰的函数
    :return: 装饰后的函数
    """

    @wraps(func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        headers = request.headers
        if 'Authorization' not in headers:
            return JsonResponse({'error': 'Invalid token'}, status=401)
        token_service = TokenService(request=request)
        token = token_service.authorization
        user_info = token_service.user_info
        body = token_service.request_body
        uuid = token_service.get_cur_uuid_by_token(token)

        system_info = PeerInfoService()
        client_info = system_info.get_peer_info_by_uuid(uuid)
        if not token_service.check_token(token):
            # Server端记录登录信息
            # LoginClientService().update_logout_status(
            #     uuid=uuid,
            #     username=user_info.username,
            #     peer_id=client_info.peer_id,
            # )
            return JsonResponse({'error': 'Invalid token'}, status=401)
        token_service.update_token(token)
        return func(request, *args, **kwargs)

    return wrapper


def request_debug_log(func):
    """
    记录请求日志的装饰器

    :param func: 被装饰的函数
    :return: 装饰后的函数
    """

    @wraps(func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        __uuid = get_randem_md5()
        request_log = {
            'method': request.method,
            'path': request.path,
            'headers': dict(request.headers),
            'client_ip': getattr(request, 'client_ip', request.META.get('CLIENT_IP') or request.META.get('REMOTE_ADDR'))
        }
        token_service = TokenService(request=request)
        if post := token_service.request_body:
            request_log['request_body'] = post
        elif get := token_service.request_query:
            request_log['request_query'] = get

        logger.debug(f'[{__uuid}]request: {json.dumps(request_log)}')

        start = time.time()
        try:
            response = func(request, *args, **kwargs)
        except Exception:
            logger.error(f'[{__uuid}]error: {traceback.format_exc()}')
            raise
        if response is None:
            response = HttpResponse(status=200)
        response_data = {
            'status_code': response.status_code,
        }
        if response.content:
            response_data['response_body'] = json.loads(response.content)
        response_log = json.dumps(response_data)
        logger.debug(f'[{__uuid}]response: {response_log}, use_time: {round(time.time() - start, 4)} s')
        return response

    return wrapper


def debug_request_None(func):
    @wraps(func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        # return func(request, *args, **kwargs)
        return HttpResponse(status=200)

    return wrapper
