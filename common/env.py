import logging
import os

from common.utils import str2bool

logger = logging.getLogger(__name__)

def get_env(key, default=None):
    return os.environ.get(key, default)


class PublicConfig:
    DB_TYPE = get_env('DATABASE', 'sqlite3')
    DEBUG = str2bool(get_env('DEBUG', False))
    APP_VERSION = get_env('APP_VERSION', '')
    SESSION_TIMEOUT = int(get_env('SESSION_TIMEOUT', 3600 * 2))


class GunicornConfig:
    # 监听地址（可由 HOST、PORT 环境变量覆盖）
    bind = f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '21114')}"

    # 进程数，线程数，默认 2 * 4
    # workers = int(get_env("WORKERS", multiprocessing.cpu_count() * 2 + 1))
    workers = int(get_env("WORKERS", 2))
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
