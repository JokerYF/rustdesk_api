import json
import os
from datetime import datetime


def log_current_env_vars(output_file=None):
    """
    记录当前环境变量到文件，用于调试目的
    """
    if output_file is None:
        from base import BASE_DIR
        output_file = BASE_DIR / 'runtime_config.json'

    # 获取所有与 RustDesk 相关的环境变量
    rustdesk_env_vars = {}
    for key, value in os.environ.items():
        if key in [
            'DATABASE', 'DEBUG', 'APP_VERSION', 'SESSION_TIMEOUT',
            'TOKEN_TIMEOUT', 'HOST', 'PORT', 'WORKERS', 'THREADS',
            'WORKER_CLASS', 'TIMEOUT', 'GRACEFUL_TIMEOUT', 'KEEPALIVE',
            'MAX_REQUESTS', 'MAX_REQUESTS_JITTER', 'LOG_LEVEL',
            'ACCESS_LOG', 'ERROR_LOG', 'TZ', 'MYSQL_HOST', 'MYSQL_PORT',
            'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE',
            'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_USER',
            'POSTGRES_PASSWORD', 'POSTGRES_DB'
        ]:
            rustdesk_env_vars[key] = value

    # 添加记录时间戳
    config_data = {
        '_recorded_at': datetime.now().isoformat(),
        '_description': 'Runtime environment variables for debugging purposes',
        'environment_variables': rustdesk_env_vars
    }

    # 确保目录存在
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)

    print(f"Runtime configuration saved to {output_file}")
    return output_file
