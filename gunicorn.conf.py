import multiprocessing
import os

from rustdesk_api.common.env import get_env

# 监听地址（可由 HOST、PORT 环境变量覆盖）
bind = f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '21114')}"

# 进程数（默认：CPU*2+1），线程数（默认：4）
workers = int(get_env("WORKERS", multiprocessing.cpu_count() * 2 + 1))
threads = int(get_env("THREADS", 4))

# 使用 gthread 以启用线程；如需纯同步可改为 "sync"
worker_class = os.getenv("WORKER_CLASS", "gthread")

# 性能与稳定性相关
preload_app = True
timeout = int(get_env("TIMEOUT", 120))
graceful_timeout = int(get_env("GRACEFUL_TIMEOUT", 30))
keepalive = int(get_env("KEEPALIVE", 5))
max_requests = int(get_env("MAX_REQUESTS", 2000))
max_requests_jitter = int(get_env("MAX_REQUESTS_JITTER", 200))

# 日志配置（同时输出到控制台与日志文件）
loglevel = os.getenv("LOG_LEVEL", "info")
# 仍设置为 "-" 以保持标准流输出；具体多路输出由 logconfig_dict 控制
accesslog = os.getenv("ACCESS_LOG", "-")
errorlog = os.getenv("ERROR_LOG", "-")
# 捕获 worker 的 stdout/stderr 并写到 errorlog（stderr）
capture_output = True


def _logs_dir() -> str:
    """
    返回日志目录路径，若不存在则创建。

    :return: 日志目录的相对路径
    :rtype: str
    """
    d = "logs"
    os.makedirs(d, exist_ok=True)
    return d


def build_logconfig_dict() -> dict:
    """
    构建 Gunicorn 的日志配置字典，支持同时输出到控制台与文件。

    :return: 兼容 logging.config.dictConfig 的配置字典
    :rtype: dict
    """
    logs_dir = _logs_dir()
    log_file = os.getenv("GUNICORN_ERROR_LOG_FILE", os.path.join(logs_dir, "gunicorn.log"))
    access_file = os.getenv("GUNICORN_ACCESS_LOG_FILE", os.path.join(logs_dir, "gunicorn_access.log"))

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
            "gunicorn": {
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
        "[gunicorn] starting with workers=%s, threads=%s, worker_class=%s, bind=%s",
        workers,
        threads,
        worker_class,
        bind,
    )


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
    worker.log.info("[gunicorn] worker spawned (pid=%s)", worker.pid)
