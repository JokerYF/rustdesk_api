from django.db import models

# Create your models here.
class SystemInfo(models.Model):
    """
    系统信息模型
    
    :param cpu: CPU型号及核心配置
    :param hostname: 主机名称
    :param memory: 内存容量
    :param os: 操作系统版本
    :param username: 系统用户名
    :param uuid: 设备唯一标识
    :param version: 客户端版本号
    """
    client_id = models.CharField(max_length=255, verbose_name='客户端ID')
    cpu = models.TextField(verbose_name='CPU信息')
    hostname = models.CharField(max_length=255, verbose_name='主机名')
    memory = models.CharField(max_length=50, verbose_name='内存')
    os = models.TextField(verbose_name='操作系统')
    username = models.CharField(max_length=255, verbose_name='用户名')
    uuid = models.CharField(max_length=255, unique=True, verbose_name='设备UUID')
    version = models.CharField(max_length=50, verbose_name='客户端版本')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='记录时间')

    class Meta:
        verbose_name = '系统信息'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        db_table = 'system_info'

    def __str__(self):
        return f'{self.hostname} ({self.uuid})'


class HeartBeat(models.Model):
    client_id = models.CharField(max_length=255)
    modified_at = models.DateTimeField()
    uuid = models.CharField(max_length=255)
    timestamp = models.DateTimeField()
    ver = models.CharField(max_length=255, default='', null=True)

    class Meta:
        ordering = ['-modified_at']
        db_table = 'heartbeat'

class Token(models.Model):
    username = models.CharField(max_length=255, verbose_name='用户名')
    uuid = models.CharField(max_length=255, verbose_name='设备UUID')
    token = models.CharField(max_length=255, verbose_name='令牌')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    last_used_at = models.DateTimeField(auto_now=True, verbose_name='最后使用时间')

    class Meta:
        verbose_name = '令牌'
        verbose_name_plural = '令牌'
        ordering = ['-created_at']
        db_table = 'token'

class LoginLog(models.Model):
    username = models.CharField(max_length=255, verbose_name='用户名')
    client_id = models.CharField(max_length=255, verbose_name='客户端ID')
    uuid = models.CharField(max_length=255, verbose_name='设备UUID')
    auto_login = models.BooleanField(default=False, verbose_name='自动登录')
    login_type = models.CharField(max_length=50, verbose_name='登录类型')
    os = models.CharField(max_length=50, verbose_name='操作系统')
    device_type = models.CharField(max_length=50, verbose_name='设备类型')
    device_name = models.CharField(max_length=255, verbose_name='设备名称')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='登录时间')

    class Meta:
        verbose_name = '登录日志'
        verbose_name_plural = '登录日志'
        ordering = ['-created_at']
        db_table = 'login_log'

    def __str__(self):
        return f'{self.username} ({self.uuid})'

