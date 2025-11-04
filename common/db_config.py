import logging
import os

from base import DATA_PATH
from common.env import DBConfig

logger = logging.getLogger(__name__)

sqlite3_config = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': os.path.join(DATA_PATH, 'db.sqlite3'),
    # 提升并发写入的容错时间（秒），避免短时锁竞争即报错
    'OPTIONS': {
        'timeout': 10,
    }
}

mysql_config = {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': DBConfig.MYSQL_DATABASE,
    'USER': DBConfig.MYSQL_USER,
    'PASSWORD': DBConfig.MYSQL_PASSWORD,
    'HOST': DBConfig.MYSQL_HOST,
    'PORT': DBConfig.MYSQL_PORT,
}


def db_config():
    if DBConfig.DB_TYPE == 'sqlite3':
        DATA_PATH.mkdir(exist_ok=True, parents=True)
        config = sqlite3_config
    elif DBConfig.DB_TYPE == 'mysql':
        config = mysql_config
    else:
        raise Exception('DB_TYPE 配置错误')
    logger.info(f'DB_TYPE: {DBConfig.DB_TYPE} - {config}')
    print(f'DB_TYPE: {DBConfig.DB_TYPE} - {config}')
    return config


database_config = db_config()
