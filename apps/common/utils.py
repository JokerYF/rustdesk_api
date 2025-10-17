from django.utils import timezone


def get_local_time():
    """
    获取当前本地时间
    
    :return: 本地化的当前时间
    """
    now = timezone.now()
    local_time = timezone.localtime(now)
    return local_time
