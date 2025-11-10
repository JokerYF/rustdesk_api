import logging
from typing import Optional

from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.utils.functional import SimpleLazyObject

from apps.db.service import TokenService


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


class StrictSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        session_key = request.COOKIES.get('sessionid')

        if session_key:
            try:
                session = Session.objects.get(session_key=session_key)
                if session.expire_date <= timezone.now():
                    # session 已过期，不允许创建新 session
                    request.session.flush()
                    return HttpResponseForbidden("Session 已过期，请重新登录")
            except Session.DoesNotExist:
                # sessionid 不存在，不允许创建新的 session
                request.session.flush()
                return HttpResponseForbidden("不允许创建新 session")
        else:
            # 没有 sessionid，不允许创建 session
            return HttpResponseForbidden("缺少 sessionid，不允许创建新 session")

        response = self.get_response(request)
        return response


class TokenAuthMiddleware:
    """
    基于 Authorization 的用户识别中间件，使 ``login_required`` 兼容 Token 方案。

    工作方式：

    - 若 ``request.user`` 已认证，则直接放行；
    - 若请求头包含 ``Authorization: Bearer <sid>_<username>``：
      - 使用 ``TokenService.check_token`` 校验令牌与会话有效性；
      - 若通过，则解析并注入对应的 ``User`` 到 ``request.user``；
    - 若无令牌或校验失败，则保持原状（继续走 Django 默认认证流程）。

    这样，使用 ``@login_required`` 的视图同样可以识别并放行携带有效 Authorization 的请求。

    :param get_response: 下一个中间件/视图的可调用对象
    :type get_response: callable
    :returns: 可调用的请求处理器
    :rtype: callable
    """

    logger = logging.getLogger(__name__)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 已有认证则无需处理（例如标准 Django 登录态）
        try:
            if getattr(request, "user", None) and request.user.is_authenticated:
                return self.get_response(request)
        except Exception:
            # 异常情况下继续尝试基于 Token 注入
            pass

        # 基于 Authorization 的 Token 注入用户
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token_service = TokenService(request=request)
                token = token_service.authorization  # 去掉 "Bearer "
                if token and token_service.check_token(token):
                    # 获取用户对象
                    user_obj = token_service.user_info
                    if isinstance(user_obj, User):
                        # 覆盖 request.user，使 login_required 生效
                        request._cached_user = user_obj
                        request.user = SimpleLazyObject(lambda: user_obj)
                        # 成功鉴权后，执行滑动续期
                        try:
                            token_service.update_token(token)
                        except Exception:
                            self.logger.debug("update_token failed for %s", token, exc_info=True)
            except Exception as e:
                # 不抛出，避免影响非 Token 请求；记录调试日志
                self.logger.debug("TokenAuthMiddleware error: %s", e, exc_info=True)

        return self.get_response(request)
