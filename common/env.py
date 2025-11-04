import logging
import os

from common.utils import str2bool

logger = logging.getLogger(__name__)


def get_env(key, default=None):
    value = os.environ.get(key, default)
    return value


class PublicConfig:
    DEBUG = str2bool(get_env('DEBUG', False))
    APP_VERSION = get_env('APP_VERSION', '')


class DBConfig:
    """数据库配置"""
    DB_TYPE = get_env('DATABASE', 'sqlite3').lower()  # sqlite3, mysql
    MYSQL_DATABASE = get_env('MYSQL_DATABASE', 'rustdesk_api')
    MYSQL_HOST = get_env('MYSQL_HOST', '127.0.0.1')
    MYSQL_PORT = get_env('MYSQL_PORT', '3306')
    MYSQL_USER = get_env('MYSQL_USER', 'root')
    MYSQL_PASSWORD = get_env('MYSQL_PASSWORD', '')


class GunicornConfig:
    # 监听地址（可由 HOST、PORT 环境变量覆盖）
    bind = f"{get_env('HOST', '0.0.0.0')}:{get_env('PORT', '21114')}"

    # 进程数，线程数，默认 2 * 4
    # workers = int(get_env("WORKERS", multiprocessing.cpu_count() * 2 + 1))
    workers = int(get_env("WORKERS", 2))
    threads = int(get_env("THREADS", 4))

    # 使用 gthread 以启用线程；如需纯同步可改为 "sync"
    worker_class = get_env("WORKER_CLASS", "gthread")

    # 性能与稳定性相关
    preload_app = True
    timeout = int(get_env("TIMEOUT", 120))
    graceful_timeout = int(get_env("GRACEFUL_TIMEOUT", 30))
    keepalive = int(get_env("KEEPALIVE", 5))
    max_requests = int(get_env("MAX_REQUESTS", 2000))
    max_requests_jitter = int(get_env("MAX_REQUESTS_JITTER", 200))

    # 日志配置（同时输出到控制台与日志文件）
    loglevel = get_env("LOG_LEVEL", "info")
    # 仍设置为 "-" 以保持标准流输出；具体多路输出由 logconfig_dict 控制
    accesslog = get_env("ACCESS_LOG", "-")
    errorlog = get_env("ERROR_LOG", "-")
    # 捕获 worker 的 stdout/stderr 并写到 errorlog（stderr）
    capture_output = True
