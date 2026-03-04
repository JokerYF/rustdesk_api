import os

from base import DATA_PATH
from common.env import PublicConfig

sqlite3_config = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': os.path.join(DATA_PATH, 'db.sqlite3'),
    'OPTIONS': {
        'timeout': 30,
        'init_command': (
            "PRAGMA journal_mode=WAL;"
            "PRAGMA busy_timeout=30000;"
            "PRAGMA synchronous=NORMAL;"
            "PRAGMA cache_size=-64000;"  # 64 MB page cache
            "PRAGMA wal_autocheckpoint=100;"
        ),
    }
}


def _apply_sqlite_pragmas(sender, connection, **kwargs):
    """在每条 SQLite 连接建立时执行 PRAGMA。"""
    if connection.vendor != 'sqlite':
        return
    cursor = connection.cursor()
    for pragma in sqlite3_config['OPTIONS']['init_command'].split(';'):
        pragma = pragma.strip()
        if pragma:
            cursor.execute(pragma)


def db_config():
    if PublicConfig.DB_TYPE == 'sqlite3':
        DATA_PATH.mkdir(exist_ok=True, parents=True)

        from django.db.backends.signals import connection_created
        connection_created.connect(_apply_sqlite_pragmas)

        return sqlite3_config
    return None
