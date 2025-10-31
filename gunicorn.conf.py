import os

from base import LOG_PATH
from rustdesk_api.common.env import GunicornConfig, PublicConfig

# 监听地址（可由 HOST、PORT 环境变量覆盖）
bind = GunicornConfig.bind

# 进程数（默认：CPU*2+1），线程数（默认：4）
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
access_log_format = '%(h)s %({x-forwarded-for}i)s %({x-real-ip}i)s - %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

def build_logconfig_dict() -> dict:
    """
    构建 Gunicorn 的日志配置字典，支持同时输出到控制台与文件。

    :return: 兼容 logging.config.dictConfig 的配置字典
    :rtype: dict
    """
    log_file = os.getenv("GUNICORN_ERROR_LOG_FILE", os.path.join(LOG_PATH, "gunicorn.log"))
    access_file = os.getenv("GUNICORN_ACCESS_LOG_FILE", os.path.join(LOG_PATH, "gunicorn_access.log"))

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "generic": {
                "format": "%(asctime)s [%(process)d] [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "access": {
                "format": "%(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "generic",
                "stream": "ext://sys.stdout",
            },
            "log_file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "formatter": "generic",
                "filename": log_file,
                "encoding": "utf8",
                "when": "midnight",
                "backupCount": 7,
                "delay": True,
            },
            "access_file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "formatter": "access",
                "filename": access_file,
                "encoding": "utf8",
                "when": "midnight",
                "backupCount": 7,
                "delay": True,
            },
        },
        "loggers": {
            # Gunicorn 自身错误日志（含应用捕获的 stderr 等）
            "gunicorn.error": {
                "level": loglevel.upper(),
                "handlers": ["console", "log_file"],
                "propagate": False,
            },
            # Gunicorn 访问日志
            "gunicorn.access": {
                "level": "INFO",
                "handlers": ["console", "access_file"],
                "propagate": False,
            },
        },
    }


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
    server.log.info(f'[gunicorn] Django DB type: {PublicConfig.DB_TYPE}')
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
