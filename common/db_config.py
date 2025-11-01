import os

from base import DATA_PATH
from common.env import PublicConfig

sqlite3_config = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': os.path.join(DATA_PATH, 'db.sqlite3'),
    # 提升并发写入的容错时间（秒），避免短时锁竞争即报错
    'OPTIONS': {
        'timeout': 10,
    }
}


def db_config():
    if PublicConfig.DB_TYPE == 'sqlite3':
        DATA_PATH.mkdir(exist_ok=True, parents=True)
        return sqlite3_config
    return None
