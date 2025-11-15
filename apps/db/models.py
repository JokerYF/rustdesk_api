from django.contrib.auth.models import User, Group, AbstractUser
from django.db import models

from common.utils import get_uuid


# Create your models here.

class HeartBeat(models.Model):
    """
    心跳测试模型
    """
    peer_id = models.CharField(max_length=255, verbose_name='客户端ID', unique=True)
    modified_at = models.DateTimeField(verbose_name='修改时间')
    uuid = models.CharField(max_length=255, verbose_name='设备UUID', unique=True)
    timestamp = models.DateTimeField(verbose_name='记录时间')
    ver = models.CharField(max_length=255, default='', null=True, verbose_name='版本号')

    class Meta:
        verbose_name = '心跳测试'
        verbose_name_plural = verbose_name
        ordering = ['-modified_at']
        db_table = 'heartbeat'
        unique_together = [['uuid', 'peer_id']]


class PeerInfo(models.Model):
    """
    客户端上报的客户端信息模型
    """
    peer_id = models.CharField(max_length=255, verbose_name='客户端ID', unique=True)
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
        verbose_name = '客户端上报的客户端信息'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        db_table = 'peer_info'
        unique_together = [['uuid', 'peer_id']]

    def __str__(self):
        return f'{self.device_name}-({self.uuid})'


class Personal(models.Model):
    """
    地址簿
    """
    guid = models.CharField(max_length=50, verbose_name='GUID', default=get_uuid, unique=True)
    personal_name = models.CharField(max_length=50, verbose_name='地址簿名称')
    create_user = models.ForeignKey(User, to_field='id', on_delete=models.CASCADE, related_name='personal_create_user')
    personal_type = models.CharField(verbose_name='地址簿类型', default='public',
                                     choices=[('public', '公开'), ('private', '私有')])
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '地址簿'
        verbose_name_plural = '地址簿'
        ordering = ['-created_at']
        db_table = 'personal'
        unique_together = [['personal_name', 'create_user']]


class Tag(models.Model):
    """
    标签模型
    """
    # id = models.AutoField(primary_key=True)
    tag = models.CharField(max_length=255, verbose_name='标签名称')
    color = models.CharField(max_length=50, verbose_name='标签颜色')
    guid = models.CharField(max_length=50, verbose_name='GUID')

    class Meta:
        verbose_name = '标签'
        db_table = 'tag'
        unique_together = [['tag', 'guid']]

    def __str__(self):
        return f'{self._meta.db_table}--{self.tag, self.color, self.guid}'


class ClientTags(models.Model):
    """
    标签模型
    """
    user = models.ForeignKey(User, to_field='id', on_delete=models.CASCADE, verbose_name='用户名',
                             related_name='user_tags')
    peer_id = models.CharField(max_length=255, verbose_name='设备ID')
    tags = models.CharField(max_length=255, verbose_name='标签名称')
    guid = models.CharField(max_length=50, verbose_name='GUID')

    class Meta:
        verbose_name = '标签'
        db_table = 'client_tags'
        unique_together = [['peer_id', 'guid']]

    def __str__(self):
        return f'{self._meta.db_table}--{self.user, self.peer_id, self.tags, self.guid}'


class Token(models.Model):
    """
    令牌模型
    """
    username = models.ForeignKey(User, to_field='id', on_delete=models.CASCADE, verbose_name='用户名')
    # username = models.ForeignKey(User, to_field='id', on_delete=models.CASCADE, verbose_name='用户名')
    # uuid = models.ForeignKey(PeerInfo, to_field='id', on_delete=models.CASCADE, verbose_name='设备ID')
    uuid = models.CharField(max_length=255, verbose_name='设备UUID')
    token = models.CharField(max_length=255, verbose_name='令牌')
    client_type = models.CharField(max_length=255, verbose_name='客户端类型',
                                   choices=[(1, 'web'), (2, 'client'), (3, 'api')], default='client')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    last_used_at = models.DateTimeField(auto_now=True, verbose_name='最后使用时间')

    class Meta:
        verbose_name = '令牌'
        verbose_name_plural = '令牌'
        ordering = ['-created_at']
        db_table = 'token'
        unique_together = [['username', 'uuid']]

    def __str__(self):
        return f'{self.username} ({self.uuid}-{self.token})'


class LoginClient(models.Model):
    """
    登录客户端模型
    """
    username = models.ForeignKey(User, to_field='id', on_delete=models.CASCADE, verbose_name='用户名')
    peer_id = models.CharField(max_length=255, verbose_name='客户端ID')
    # uuid = models.ForeignKey(PeerInfo, to_field='id', on_delete=models.CASCADE, verbose_name='设备ID')
    uuid = models.CharField(max_length=255, verbose_name='设备UUID')
    client_type = models.CharField(max_length=255, verbose_name='客户端类型',
                                   choices=[(1, 'web'), (2, 'client')], default=2)
    platform = models.CharField(max_length=255, verbose_name='平台',
                                choices=[(1, 'Windows'), (2, 'MacOS'), (3, 'Linux'), (4, 'Android'), (5, 'iOS'),
                                         (6, 'Web')],
                                null=True)
    client_name = models.CharField(max_length=255, verbose_name='客户端名称', default='', blank=True)
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
    username = models.ForeignKey(User, to_field='id', on_delete=models.CASCADE, verbose_name='用户名', null=True,
                                 default='')
    uuid = models.ForeignKey(PeerInfo, to_field='id', on_delete=models.CASCADE, verbose_name='设备ID')
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
    controller_uuid = models.ForeignKey(PeerInfo, to_field='id', on_delete=models.CASCADE,
                                        verbose_name='控制端ID', related_name='auditlog_controller', null=True)
    controlled_uuid = models.ForeignKey(PeerInfo, to_field='id', on_delete=models.CASCADE,
                                        verbose_name='被控端ID', related_name='auditlog_controlled')
    type = models.IntegerField(verbose_name='类型', default=0)
    username = models.ForeignKey(User, to_field='id', on_delete=models.CASCADE, max_length=50,
                                 verbose_name='发起连接的用户', null=True)
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
    controller_uuid = models.ForeignKey(PeerInfo, to_field='id', on_delete=models.CASCADE, max_length=255,
                                        verbose_name='控制端ID', related_name='auditfile_controller')
    controlled_uuid = models.ForeignKey(PeerInfo, to_field='id', on_delete=models.CASCADE, max_length=255,
                                        verbose_name='被控端ID', related_name='auditfile_controlled')
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


class UserPrefile(models.Model):
    """
    用户配置模型
    """
    user = models.OneToOneField(User, to_field='id', on_delete=models.CASCADE, related_name='userprofile')
    group = models.ForeignKey(Group, to_field='id', on_delete=models.CASCADE, related_name='userprofile_group')

    class Meta:
        verbose_name = '用户配置'
        verbose_name_plural = '用户配置'
        db_table = 'user_profile'

    def __str__(self):
        return f'{self.user.username} {self.group.name if self.group else "None"}'


class UserPersonal(models.Model):
    """
    用户与个人地址簿关系模型
    """
    user = models.ForeignKey(User, to_field='id', on_delete=models.CASCADE, related_name='user_personal')
    personal = models.ForeignKey(Personal, to_field='guid', on_delete=models.CASCADE, related_name='personal_user')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '用户与个人地址簿关系'
        verbose_name_plural = '用户与个人地址簿关系'
        ordering = ['-created_at']
        db_table = 'user_personal'


class PeerPersonal(models.Model):
    """
    设备与个人地址簿关系模型
    """
    peer = models.ForeignKey(PeerInfo, to_field='id', on_delete=models.CASCADE, related_name='peer_personal')
    personal = models.ForeignKey(Personal, to_field='guid', on_delete=models.CASCADE, related_name='personal_peer')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '设备与个人地址簿关系模型'
        verbose_name_plural = '设备与个人地址簿关系模型'
        ordering = ['-created_at']
        db_table = 'peer_personal'


class SharePersonal(models.Model):
    """
    分享地址簿记录
    """
    guid = models.CharField(max_length=50, verbose_name='guid')
    to_share_id = models.CharField(max_length=50, verbose_name='被分享者的ID，被分享者可以是用户，也可以是用户组')
    from_share_id = models.CharField(max_length=50, verbose_name='分享者的ID，分享者可以是用户，也可以是用户组')
    to_share_type = models.IntegerField(verbose_name='被分享者的类型，1:用户，2:用户组',
                                        choices=[(1, '用户'), (2, '用户组')])
    from_share_type = models.IntegerField(verbose_name='分享者的类型，1:用户，2:用户组',
                                          choices=[(1, '用户'), (2, '用户组')])
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '分享地址簿记录'
        verbose_name_plural = '分享地址簿记录'
        ordering = ['-created_at']
        db_table = 'share_personal'
        unique_together = [['guid', 'to_share_id']]  # 限定一个地址簿只能分享给同一个人一次


class Alias(models.Model):
    """
    别名模型
    """
    alias = models.CharField(max_length=50, verbose_name='别名')
    peer_id = models.ForeignKey(PeerInfo, to_field='id', on_delete=models.CASCADE,
                                related_name='alias_peer_id')
    guid = models.ForeignKey(Personal, to_field='guid', on_delete=models.CASCADE, related_name='alias_guid')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '别名'
        verbose_name_plural = '别名'
        ordering = ['-created_at']
        db_table = 'alias'
        unique_together = [['alias', 'peer_id', 'guid']]  # alias在guid中只能对一个设备进行设置


class UserConfig(models.Model):
    """
    用户配置模型
    """
    user = models.OneToOneField(User, to_field='id', on_delete=models.CASCADE, related_name='user_config')
    config_name = models.CharField(max_length=50, verbose_name='配置名称')
    config_value = models.TextField(verbose_name='配置值')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '用户配置'
        verbose_name_plural = '用户配置'
        ordering = ['-created_at']
        db_table = 'user_config'
        unique_together = [['user', 'config_name']]
