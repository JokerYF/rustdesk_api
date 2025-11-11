import os
from typing import Optional, Dict

# 通用默认参数常量，供 Django/Gunicorn 日志配置复用
DEFAULT_LOGGING_VERSION = 1
DEFAULT_DISABLE_EXISTING_LOGGERS = False
DEFAULT_ROTATE_WHEN = 'midnight'
DEFAULT_ROTATE_BACKUP_COUNT = 7
DEFAULT_FILE_ENCODING = 'utf8'
DEFAULT_HANDLER_DELAY = True


def build_timed_rotating_file_handler(filename: str, formatter: str, level: Optional[str] = None) -> dict:
    """
    构建 TimedRotatingFileHandler handler 配置。

    :param str filename: 目标日志文件绝对路径或相对路径
    :param str formatter: 使用的 formatter 名称
    :param Optional[str] level: 可选日志级别（不传则不设置）
    :return: 可用于 logging.config.dictConfig 的 handler 配置
    :rtype: dict
    """
    handler = {
        'class': 'logging.handlers.TimedRotatingFileHandler',
        'formatter': formatter,
        'filename': filename,
        'encoding': DEFAULT_FILE_ENCODING,
        'when': DEFAULT_ROTATE_WHEN,
        'backupCount': DEFAULT_ROTATE_BACKUP_COUNT,
        'delay': DEFAULT_HANDLER_DELAY,
    }
    if level is not None:
        handler['level'] = level
    return handler


def build_stream_handler(formatter: str, level: Optional[str] = None, stream: Optional[str] = None) -> dict:
    """
    构建控制台（StreamHandler）handler 配置。

    :param str formatter: 使用的 formatter 名称
    :param Optional[str] level: 可选日志级别（不传则不设置）
    :param Optional[str] stream: 可选输出流，如 'ext://sys.stdout'
    :return: 可用于 logging.config.dictConfig 的 handler 配置
    :rtype: dict
    """
    handler = {
        'class': 'logging.StreamHandler',
        'formatter': formatter,
    }
    if level is not None:
        handler['level'] = level
    if stream is not None:
        handler['stream'] = stream
    return handler


# 统一的 formatter 定义，供 Django 与 Gunicorn 复用
# 注意：保持原有格式行为，方便平滑迁移；如需统一风格，可在此处统一调整
FORMATTERS: Dict[str, dict] = {
    'default_verbose': {
        'format': '%(asctime)s [%(process)d-%(thread)d] [%(levelname)s] %(name)s: %(message)s',
    },
    'default_simple': {
        'format': '%(asctime)s [%(process)d-%(thread)d] [%(levelname)s]: %(message)s',
    },
}


def build_django_logging(debug: bool, log_dir: str, app_log_filename: str = 'rustdesk_api.log',
                         request_debug_filename: str = 'request_debug.log') -> dict:
    """
    构建 Django LOGGING 字典。

    :param bool debug: 是否开启 DEBUG，影响控制台与文件日志级别与格式
    :param str log_dir: 日志目录的绝对路径，需可写且已存在
    :param str app_log_filename: 主应用日志文件名
    :param str request_debug_filename: 请求调试日志文件名
    :return: 可直接赋值给 Django `LOGGING` 的配置字典
    :rtype: dict
    """
    app_log_file = os.path.join(log_dir, app_log_filename)
    request_log_file = os.path.join(log_dir, request_debug_filename)

    return {
        'version': DEFAULT_LOGGING_VERSION,
        'disable_existing_loggers': DEFAULT_DISABLE_EXISTING_LOGGERS,
        'formatters': {
            'verbose': FORMATTERS['default_verbose'],
            'simple': FORMATTERS['default_simple']
        },
        'handlers': {
            'file': build_timed_rotating_file_handler(
                filename=app_log_file,
                formatter='verbose',
                level='DEBUG' if debug else 'INFO',
            ),
            'request_debug_file': build_timed_rotating_file_handler(
                filename=request_log_file,
                formatter='verbose',
                level='DEBUG',
            ),
            'console': build_stream_handler(
                formatter='verbose' if debug else 'simple',
                level='DEBUG' if debug else 'INFO',
            ),
        },
        'filters': {
            'require_debug_true': {
                '()': 'django.utils.log.RequireDebugTrue',
            }
        },
        'loggers': {
            '': {
                'handlers': ['file', 'console'],
                'level': 'DEBUG' if debug else 'INFO',
                'propagate': True,
            },
            'django': {
                'handlers': ['file', 'console'],
                'level': 'INFO',
                'propagate': True,
            },
            'request_debug_log': {
                'handlers': ['console', 'request_debug_file'] if debug else ['request_debug_file'],
                'level': 'DEBUG',
                'propagate': False,
            },
        },
    }


def build_gunicorn_logging(loglevel: str, log_dir: str, error_filename: str = 'gunicorn.log',
                           access_filename: str = 'gunicorn_access.log') -> dict:
    """
    构建 Gunicorn 使用的 `logconfig_dict`。

    :param str loglevel: 错误日志级别，如 'INFO'、'WARNING'、'ERROR' 等
    :param str log_dir: 日志目录的绝对路径，需可写且已存在
    :param str error_filename: 错误日志文件名
    :param str access_filename: 访问日志文件名
    :return: 兼容 logging.config.dictConfig 的配置字典
    :rtype: dict
    """
    error_log_file = os.path.join(log_dir, error_filename)
    access_log_file = os.path.join(log_dir, access_filename)

    return {
        'version': DEFAULT_LOGGING_VERSION,
        'disable_existing_loggers': DEFAULT_DISABLE_EXISTING_LOGGERS,
        'formatters': {
            'verbose': FORMATTERS['default_verbose'],
            'simple': FORMATTERS['default_simple']
        },
        'handlers': {
            'console': build_stream_handler(
                formatter='simple',
                stream='ext://sys.stdout',
            ),
            'log_file': build_timed_rotating_file_handler(
                filename=error_log_file,
                formatter='verbose',
            ),
            'access_file': build_timed_rotating_file_handler(
                filename=access_log_file,
                formatter='verbose',
            ),
        },
        'loggers': {
            'gunicorn.error': {
                'level': str(loglevel).upper(),
                'handlers': ['console', 'log_file'],
                'propagate': False,
            },
            'gunicorn.access': {
                'level': 'INFO',
                'handlers': ['console', 'access_file'],
                'propagate': False,
            },
        },
    }
