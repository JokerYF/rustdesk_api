from typing import Optional

from django.contrib.sessions.middleware import SessionMiddleware
from django.utils.cache import patch_vary_headers


class RealIPMiddleware:
    """
    解析并注入真实客户端 IP 的中间件。

    本中间件按以下优先级解析客户端 IP：
    1) ``X-Forwarded-For``
    2) ``X-Real-IP``
    3) ``REMOTE_ADDR``

    解析结果会写入 ``request.client_ip`` 与 ``request.META['CLIENT_IP']``，
    便于业务代码与日志记录统一读取。

    :param get_response: 下一个中间件/视图的可调用对象
    :type get_response: callable
    :returns: 可调用的请求处理器
    :rtype: callable
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        client_ip = self._extract_client_ip(request)
        if client_ip:
            request.META['CLIENT_IP'] = client_ip
            # 动态属性，方便直接使用
            setattr(request, 'client_ip', client_ip)
        return self.get_response(request)

    @staticmethod
    def _extract_client_ip(request) -> Optional[str]:
        """
        提取客户端 IP，优先使用代理头部，回退到 ``REMOTE_ADDR``。

        :param request: Django 请求对象
        :type request: django.http.HttpRequest
        :returns: 提取到的 IP 字符串，若无法解析则返回 ``None``
        :rtype: Optional[str]
        """
        meta = request.META or {}

        xff = meta.get('HTTP_X_FORWARDED_FOR')
        if xff:
            # 取最左端（最原始）的客户端 IP
            parts = [p.strip() for p in xff.split(',') if p.strip()]
            if parts:
                return parts[0]

        x_real_ip = meta.get('HTTP_X_REAL_IP')
        if x_real_ip:
            return x_real_ip.strip()

        remote_addr = meta.get('REMOTE_ADDR')
        if remote_addr:
            return remote_addr.strip()

        return None


class OptOutSessionMiddleware(SessionMiddleware):
    """
    可选择跳过 session 保存的会话中间件。

    跳过 session 写入的条件（满足任一即跳过）：

    1. 请求路径以 ``/api/`` 开头 — RustDesk 客户端接口使用自定义 Token
       认证，不需要 Django Session，跳过可大幅减少 SQLite 写入。
    2. 请求头 ``X-Session-No-Renew: 1`` — 显式指示不续命（如前端轮询）。

    未命中上述条件时，行为与 Django 原生 SessionMiddleware 完全一致。
    """

    def process_response(self, request, response):
        if not hasattr(request, 'session'):
            return super().process_response(request, response)

        # /api/ 路径使用自定义 Token 认证，不需要 Django Session
        no_renew = request.path.startswith('/api/')

        if not no_renew:
            try:
                no_renew = (request.headers.get('X-Session-No-Renew') == '1')
            except Exception:
                no_renew = (request.META.get('HTTP_X_SESSION_NO_RENEW') == '1')

        if not no_renew:
            return super().process_response(request, response)

        try:
            if getattr(request.session, 'accessed', False):
                patch_vary_headers(response, ('Cookie',))
        except Exception:
            return super().process_response(request, response)

        return response
