import os

from gunicorn.glogging import Logger as GunicornLogger

from base import LOG_PATH
from common.db_config import database_config
from common.env import GunicornConfig, PublicConfig, DBConfig
from common.logging_config import build_gunicorn_logging

# 监听地址（可由 HOST、PORT 环境变量覆盖）
bind = GunicornConfig.bind

# 进程数，线程数
workers = GunicornConfig.workers
threads = GunicornConfig.threads

# 使用 gthread 以启用线程；如需纯同步可改为 "sync"
worker_class = GunicornConfig.worker_class

# 性能与稳定性相关
preload_app = GunicornConfig.preload_app
timeout = GunicornConfig.timeout
graceful_timeout = GunicornConfig.graceful_timeout
keepalive = GunicornConfig.keepalive
max_requests = GunicornConfig.max_requests
max_requests_jitter = GunicornConfig.max_requests_jitter

# 日志配置（同时输出到控制台与日志文件）
loglevel = GunicornConfig.loglevel
# 仍设置为 "-" 以保持标准流输出；具体多路输出由 logconfig_dict 控制
accesslog = GunicornConfig.accesslog
errorlog = GunicornConfig.errorlog
# 捕获 worker 的 stdout/stderr 并写到 errorlog（stderr）
capture_output = GunicornConfig.capture_output

# 访问日志格式：同时记录直连 IP 与代理转发的 IP
# %(h)s 为远端地址；%({x-forwarded-for}i)s 与 %({x-real-ip}i)s 为请求头
access_log_format = '%(h)s %({x-forwarded-for}i)s %({x-real-ip}i)s - %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" rt=%(L4)ss'


class CustomGunicornLogger(GunicornLogger):
    """
    自定义 Gunicorn Logger，扩展访问日志原子。

    - 新增原子 ``L4``：以秒为单位的响应时间，保留 4 位小数（字符串）。
    """

    def atoms(self, resp, req, environ, request_time) -> dict:
        """
        扩展原子字典，增加 ``L4``。

        :param resp: 响应对象
        :param req: 请求对象
        :param environ: WSGI 环境字典
        :param request_time: 请求耗时（秒，float）
        :return: 包含新增 ``L4`` 的原子映射
        :rtype: dict
        """
        atoms = super().atoms(resp, req, environ, request_time)
        try:
            rt = float(request_time)
        except Exception:
            try:
                rt = float(atoms.get('L', 0.0))
            except Exception:
                rt = 0.0
        atoms['L4'] = f"{rt:.4f}"
        return atoms


# 使用自定义 logger
logger_class = CustomGunicornLogger


def build_logconfig_dict() -> dict:
    """
    构建 Gunicorn 的日志配置字典，支持同时输出到控制台与文件。

    :return: 兼容 logging.config.dictConfig 的配置字典
    :rtype: dict
    """
    error_filename = os.getenv("GUNICORN_ERROR_LOG_FILE", os.path.join(LOG_PATH, "gunicorn.log"))
    access_filename = os.getenv("GUNICORN_ACCESS_LOG_FILE", os.path.join(LOG_PATH, "gunicorn_access.log"))
    # 兼容旧环境变量（若传入的是完整路径则直接使用；否则使用文件名拼接 LOG_PATH）
    if os.path.isabs(error_filename):
        err_path = error_filename
    else:
        err_path = os.path.join(LOG_PATH, os.path.basename(error_filename))
    if os.path.isabs(access_filename):
        acc_path = access_filename
    else:
        acc_path = os.path.join(LOG_PATH, os.path.basename(access_filename))

    return build_gunicorn_logging(GunicornConfig.loglevel, LOG_PATH, os.path.basename(err_path),
                                  os.path.basename(acc_path))


# 将上面的日志配置应用到 Gunicorn
logconfig_dict = build_logconfig_dict()

# 代理相关（如有反向代理可保留全部转发的 IP）
forwarded_allow_ips = os.getenv("FORWARDED_ALLOW_IPS", "*")


def on_starting(server):
    """
    Master 进程启动时回调，用于环境准备与提示日志。

    :param server: Gunicorn Server 实例
    :return: None
    """
    os.makedirs("logs", exist_ok=True)
    server.log.info(
        f"[gunicorn] starting with bind={bind}, workers={workers}, threads={threads}, worker_class={worker_class}",
    )
    server.log.info(f'[gunicorn] Django debug model: {PublicConfig.DEBUG}')
    server.log.info(f'[gunicorn] Django DB type: {DBConfig.DB_TYPE}')
    server.log.info(f'[gunicorn] Django DB config: {database_config}')
    server.log.info(f'[gunicorn] RustDesk API Version: {PublicConfig.APP_VERSION}')


def when_ready(server):
    """
    所有子进程就绪时回调。

    :param server: Gunicorn Server 实例
    :return: None
    """
    server.log.info("[gunicorn] server is ready.")


def post_fork(server, worker):
    """
    子进程 fork 后回调，适合进行与 worker 相关的初始化工作。

    :param server: Gunicorn Server 实例
    :param worker: 当前 worker 实例
    :return: None
    """
    worker.log.info(f"[gunicorn] worker spawned (pid={worker.pid})")
