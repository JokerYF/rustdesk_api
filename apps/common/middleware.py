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
    可选择跳过续命的会话中间件。

    通过请求头 ``X-Session-No-Renew: 1`` 指示该请求不应刷新会话的过期时间，
    即便全局启用了 ``SESSION_SAVE_EVERY_REQUEST``。此中间件仅在存在该请求头时
    跳过 SessionMiddleware 的默认保存逻辑，从而避免“滑动过期”续命。

    :param get_response: 下一个中间件/视图的可调用对象
    :type get_response: callable
    :returns: 可调用的请求处理器
    :rtype: callable
    :notes:
        - 仅用于“只读/无副作用”的接口（如前端轮询），不要在会修改会话状态的请求上使用该头
        - 未携带该请求头时，行为与 Django 原生 SessionMiddleware 完全一致
    """

    def process_response(self, request, response):
        # 未创建/未访问 session：交给父类处理（或直接返回）
        if not hasattr(request, 'session'):
            return super().process_response(request, response)

        # 识别显式禁续命的请求（兼容 META 中的标准化头部）
        no_renew = False
        try:
            # Django 5+ 提供 request.headers 取大小写无关头
            no_renew = (request.headers.get('X-Session-No-Renew') == '1')
        except Exception:
            no_renew = (request.META.get('HTTP_X_SESSION_NO_RENEW') == '1')

        if not no_renew:
            # 正常请求：沿用原生行为
            return super().process_response(request, response)

        # 禁续命请求：
        # 仅维护 Vary: Cookie（若访问过 session），但不触发保存与设置新 Cookie，
        # 从而避免在 SAVE_EVERY_REQUEST=True 情况下“续命”。
        try:
            if getattr(request.session, 'accessed', False):
                patch_vary_headers(response, ('Cookie',))
        except Exception:
            # 安全兜底：如 session 对象异常，仍回退到父类逻辑
            return super().process_response(request, response)

        # 不保存、不更新 Cookie，直接返回响应
        return response
