from django.contrib.auth.models import User
from django.db import models


# Create your models here.

class HeartBeat(models.Model):
    client_id = models.CharField(max_length=255, verbose_name='客户端ID')
    modified_at = models.DateTimeField(verbose_name='修改时间')
    uuid = models.CharField(max_length=255, verbose_name='设备UUID', unique=True)
    timestamp = models.DateTimeField(verbose_name='记录时间')
    ver = models.CharField(max_length=255, default='', null=True, verbose_name='版本号')

    class Meta:
        ordering = ['-modified_at']
        db_table = 'heartbeat'


class SystemInfo(models.Model):
    """
    系统信息模型
    
    :param cpu: CPU型号及核心配置
    :param device_name: 主机名称
    :param memory: 内存容量
    :param os: 操作系统版本
    :param username: 系统用户名
    :param uuid: 设备唯一标识
    :param version: 客户端版本号
    """
    client_id = models.CharField(max_length=255, verbose_name='客户端ID')
    cpu = models.TextField(verbose_name='CPU信息')
    device_name = models.CharField(max_length=255, verbose_name='主机名')
    memory = models.CharField(max_length=50, verbose_name='内存')
    os = models.TextField(verbose_name='操作系统')
    username = models.CharField(max_length=255, verbose_name='用户名')
    uuid = models.CharField(max_length=255, unique=True, verbose_name='设备UUID')
    # uuid = models.ForeignKey(HeartBeat, to_field='uuid', on_delete=models.CASCADE, verbose_name='设备UUID')
    version = models.CharField(max_length=50, verbose_name='客户端版本')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='记录时间')

    class Meta:
        verbose_name = '系统信息'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        db_table = 'system_info'

    def __str__(self):
        return f'{self.device_name} ({self.uuid})'


class Tag(models.Model):
    """
    标签模型

    :param tag: 标签名称
    :param color: 标签描述
    """
    id = models.AutoField(primary_key=True)
    tag = models.CharField(max_length=255, unique=True, verbose_name='标签名称')
    color = models.CharField(max_length=50, verbose_name='标签颜色')

    class Meta:
        verbose_name = '标签'
        db_table = 'tag'

    def __str__(self):
        return self.tag


class TagToClient(models.Model):
    tag_id = models.ForeignKey(Tag, to_field='id', on_delete=models.CASCADE, verbose_name='标签')
    client = models.ForeignKey(SystemInfo, to_field='uuid', on_delete=models.CASCADE, verbose_name='设备UUID')

    class Meta:
        verbose_name = '标签与设备关系'
        verbose_name_plural = '标签与设备关系'
        db_table = 'tag_to_client'


class UserToTag(models.Model):
    username = models.ForeignKey(User, to_field='username', on_delete=models.CASCADE, verbose_name='用户名')
    tag_id = models.ForeignKey(Tag, to_field='id', on_delete=models.CASCADE, verbose_name='标签')

    class Meta:
        verbose_name = '用户与标签关系'
        verbose_name_plural = '用户与标签关系'
        db_table = 'user_to_tag'


class Token(models.Model):
    username = models.ForeignKey(User, to_field='username', on_delete=models.CASCADE, verbose_name='用户名')
    # username = models.ForeignKey(User, to_field='username', on_delete=models.CASCADE, verbose_name='用户名')
    uuid = models.ForeignKey(SystemInfo, to_field='uuid', on_delete=models.CASCADE, verbose_name='设备UUID')
    token = models.CharField(max_length=255, verbose_name='令牌')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    last_used_at = models.DateTimeField(auto_now=True, verbose_name='最后使用时间')

    class Meta:
        verbose_name = '令牌'
        verbose_name_plural = '令牌'
        ordering = ['-created_at']
        db_table = 'token'

    def __str__(self):
        return f'{self.username} ({self.uuid}-{self.token})'


class LoginClient(models.Model):
    username = models.ForeignKey(User, to_field='username', on_delete=models.CASCADE, verbose_name='用户名')
    client_id = models.CharField(max_length=255, verbose_name='客户端ID')
    uuid = models.ForeignKey(SystemInfo, to_field='uuid', on_delete=models.CASCADE, verbose_name='设备UUID')
    login_status = models.BooleanField(default=True, verbose_name='登录状态')

    class Meta:
        verbose_name = '登录客户端'
        verbose_name_plural = '登录客户端'
        ordering = ['-username']
        db_table = 'login_client'


class Log(models.Model):
    """
    日志模型
    """
    username = models.ForeignKey(User, to_field='username', on_delete=models.CASCADE, verbose_name='用户名', null=True,
                                 default='')
    uuid = models.ForeignKey(SystemInfo, to_field='uuid', on_delete=models.CASCADE, verbose_name='设备UUID')
    log_level = models.CharField(max_length=50, verbose_name='日志类型',
                                 choices=[('info', '信息'), ('warning', '警告'), ('error', '错误')])
    operation_type = models.CharField(max_length=50, verbose_name='操作类型',
                                      choices=[('add', '添加'), ('delete', '删除'), ('update', '更新'),
                                               ('query', '查询'), ('other', '其他')])
    operation_object = models.CharField(max_length=50, verbose_name='操作对象',
                                        choices=[('tag', '标签'), ('client', '设备'), ('user', '用户'),
                                                 ('token', '令牌'), ('login_client', '登录客户端'),
                                                 ('login_log', '登录日志'), ('log', '日志'),
                                                 ('tag_to_client', '标签与设备关系'), ('user_to_tag', '用户与标签关系'),
                                                 ('system_info', '系统信息'), ('heart_beat', '心跳包'),
                                                 ('config', '配置'), ('file', '文件'),
                                                 ('file_to_client', '文件与设备关系'),
                                                 ('file_to_tag', '文件与标签关系'), ('file_to_user', '文件与用户关系'),
                                                 ('file_to_file', '文件与文件关系')])
    operation_result = models.CharField(max_length=50, verbose_name='操作结果',
                                        choices=[('success', '成功'), ('fail', '失败')])
    operation_detail = models.TextField(verbose_name='操作详情', null=True, default='')
    operation_time = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')

    class Meta:
        verbose_name = '日志'
        verbose_name_plural = '日志'
        ordering = ['-operation_time']
        db_table = 'log'


class AutidConnLog(models.Model):
    """
    审计日志模型
    """
    action = models.CharField(max_length=50, verbose_name='操作类型')
    conn_id = models.IntegerField(verbose_name='连接ID')
    initiating_ip = models.CharField(max_length=50, verbose_name='发起IP')
    session_id = models.CharField(max_length=50, verbose_name='会话ID', null=True)
    controller_uuid = models.ForeignKey(SystemInfo, to_field='uuid', on_delete=models.CASCADE,
                                        verbose_name='控制端UUID', related_name='auditlog_controller', null=True)
    controlled_uuid = models.ForeignKey(SystemInfo, to_field='uuid', on_delete=models.CASCADE,
                                        verbose_name='被控端UUID', related_name='auditlog_controlled')
    type = models.IntegerField(verbose_name='类型')
    username = models.ForeignKey(User, to_field='username', on_delete=models.CASCADE, max_length=50,
                                 verbose_name='用户名', null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '审计日志'
        verbose_name_plural = '审计日志'
        ordering = ['-created_at']
        db_table = 'audit_log'


class AuditFileLog(models.Model):
    """
    审计文件模型
    """
    conn_id = models.IntegerField(verbose_name='连接ID')
    controller_uuid = models.ForeignKey(SystemInfo, to_field='uuid', on_delete=models.CASCADE, max_length=255,
                                        verbose_name='控制端UUID', related_name='auditfile_controller')
    controlled_uuid = models.ForeignKey(SystemInfo, to_field='uuid', on_delete=models.CASCADE, max_length=255,
                                        verbose_name='被控端UUID', related_name='auditfile_controlled')
    operation_type = models.IntegerField(verbose_name='操作类型', default=1)
    operation_info = models.CharField(verbose_name='操作信息', null=True, default='')
    is_file = models.BooleanField(verbose_name='是否文件')
    remote_path = models.CharField(verbose_name='远程路径', null=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '审计文件'
        verbose_name_plural = '审计文件'
        ordering = ['-created_at']
        db_table = 'audit_file'
