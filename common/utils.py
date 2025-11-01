import random
import time
from hashlib import md5
from uuid import uuid1, uuid4

from django.utils import timezone


def get_local_time():
    """
    获取当前本地时间
    
    :return: 本地化的当前时间
    """
    now = timezone.now()
    local_time = timezone.localtime(now)
    return local_time


def get_uuid():
    """
    获取一个UUID

    :return: UUID
    """
    return uuid1()


def get_uuid_str():
    return get_uuid().hex


def get_md5(data: str):
    """
    获取一个md5
    :param data:
    :return:
    """
    return md5(data.encode('utf-8')).hexdigest()


def get_randem_md5():
    """
    获取一个随机的MD5
    :return:
    """
    return str(get_md5(f'{uuid4()}_{time.ctime()}_{random.randint(0, 99999999)}'))


def str2bool(value):
    if isinstance(value, bool):
        return value
    return value.lower() in ('true', 't', '1')
