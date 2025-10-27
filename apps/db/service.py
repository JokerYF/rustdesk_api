import json
import logging
from datetime import timedelta
from typing import TypeVar

from django.contrib.auth.models import User, Group, Permission
from django.db import models
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.common.utils import get_local_time, get_randem_md5
from apps.db.models import HeartBeat, SystemInfo, Token, LoginClient, TagToClient, Tag, UserToTag, Log, AutidConnLog, \
    UserPrefile

logger = logging.getLogger(__name__)

# 定义泛型类型变量，用于表示各种模型类型
ModelType = TypeVar('ModelType', bound=models.Model)


class BaseService:
    """
    数据服务基类
    
    :param db: 需要操作的模型类
    """
    db: models.Model = None

    def get_list(self, **kwargs):
        """
        通用分页查询方法

        :param filters: 查询条件字典
        :param ordering: 排序字段列表
        :param page: 当前页码
        :param page_size: 每页记录数
        :return: 包含分页信息的字典
        """
        page = int(kwargs.pop('page', 1))
        page_size = int(kwargs.pop('page_size', 10))

        filters = kwargs.pop('filters', {})
        queryset = self.db.objects.filter(**filters)

        if ordering := kwargs.pop('ordering', []):
            queryset = queryset.order_by(*ordering)

        total = queryset.count()
        results = queryset[(page - 1) * page_size: page * page_size]

        return {
            'results': results,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }

    def create(self, **kwargs) -> ModelType:
        """
        创建新记录
        
        :param kwargs: 记录字段键值对
        :return: 新创建的模型实例
        """
        return self.db.objects.create(**kwargs)

    def delete(self, *args, **kwargs):
        """
        根据ID删除记录
        
        :param record_id: 记录ID
        :return: 删除的记录数
        """
        return self.db.objects.filter(*args, **kwargs).delete()

    def query(self, *args, **kwargs) -> QuerySet:
        """
        通用条件查询
        
        :param args: Q查询对象
        :param kwargs: 查询条件
        :return: 查询结果集合
        """
        return self.db.objects.filter(*args, **kwargs)

    def create_or_update(self, filters: dict, **kwargs):
        """
        通用更新方法（根据模型设计可能需要重写）
        
        :param filters: 过滤条件字典
        :param kwargs: 更新字段键值对
        :return: 更新后的模型实例
        
        自动处理类型转换：
        - 将modified_at时间戳转换为datetime对象
        """
        # logger.debug(f'update filters: {filters}, kwargs: {kwargs}')
        if not self.db.objects.filter(**filters).update(**kwargs):
            data = {
                **filters,
                **kwargs
            }
            self.create(**data)

    def update(self, filters: dict, **kwargs):
        return self.db.objects.filter(**filters).update(**kwargs)

    @staticmethod
    def get_username(username):
        if isinstance(username, str):
            username = UserService().get_user_by_name(username)
        return username

    @staticmethod
    def get_uuid(uuid):
        if isinstance(uuid, str):
            uuid = SystemInfoService().get_client_info_by_uuid(uuid)
        return uuid


class UserService(BaseService):
    db = User

    def get(self, email) -> User | None:
        try:
            return self.db.objects.get(email=email)
        except self.db.DoesNotExist:
            return None

    def get_users(self, *users):
        return self.db.objects.filter(username__in=[*users]).all()

    def create_user(self, username, password, email='', is_superuser=False, is_staff=False,
                    group: str | Group = None) -> User:
        user = self.create(
            username=username,
            email=email,
            is_superuser=is_superuser,
            is_staff=is_staff,
        )
        user.set_password(password)
        user.save()
        logger.info(f'创建用户: {user}')

        # 添加用户到组（确保参数顺序正确）
        group_service = GroupService()
        group_service.add_user_to_group(user, group_name=group)

        return user

    def get_user_by_email(self, email) -> User:
        return self.query(email=email).first()

    def get_user_by_name(self, username) -> User:
        if isinstance(username, User):
            return username
        return self.query(username=username).first()

    def set_password(self, password, email=None, username=None):
        if username is not None:
            user = self.get_user_by_name(username)
        elif email is not None:
            user = self.get_user_by_email(email)
        else:
            raise ValueError("Either username or email must be provided.")
        user.set_password(password)
        user.save()
        logger.info(f'设置用户密码: {user}')
        return user

    def __get_list(self, **kwargs):
        """
        通用分页查询方法

        :param filters: 查询条件字典
        :param ordering: 排序字段列表
        :param page: 当前页码
        :param page_size: 每页记录数
        :return: 包含分页信息的字典
        """
        page = int(kwargs.pop('page', 1))
        page_size = int(kwargs.pop('page_size', 10))

        filters = kwargs.pop('filters', {})
        queryset = self.db.objects.filter(**filters)

        if ordering := kwargs.pop('ordering', []):
            queryset = queryset.order_by(*ordering)

        total = queryset.count()
        results = queryset[(page - 1) * page_size: page * page_size]

        return {
            'results': results,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }

    def get_list_by_status(self, status, page=1, page_size=10):
        return self.__get_list(status=status, page=page, page_size=page_size)

    def get_guid(self, username):
        user = self.get_user_by_name(username)
        group_id = user.userprofile.group_id
        collection_id = 1 if user.is_superuser else 0
        return f'{group_id}-{user.id}-{collection_id}'

    def parse_guid(self, guid):
        guid_list = guid.split('-')
        group_id = guid_list[0]
        user_id = guid_list[1]
        collection_id = guid_list[2]
        group = GroupService().get_group_by_id(group_id)
        user = self.get_user_by_id(user_id)
        return group, user, bool(int(collection_id))  # TODO 第三个值应该返回地址簿ID，这里需要改

    def set_user_permissions(self, username, *permissions):
        permissions = self.db.objects.filter(user_permissions__codename__in=[*permissions])
        user = self.get_user_by_name(username)
        if user:
            user.user_permissions.add(*permissions)

    def del_user_permissions(self, username, *permissions):
        permissions = self.db.objects.filter(user_permissions__codename__in=[*permissions])

        user = self.get_user_by_name(username)
        if user:
            user.user_permissions.remove(*permissions)

    def get_user_permissions(self, username):
        user = self.get_user_by_name(username)
        if user:
            return user.user_permissions.all()
        return None

    def is_user_has_permission(self, username, *permissions) -> bool:
        permissions = self.db.objects.filter(user_permissions__codename__in=[*permissions])
        user = self.get_user_by_name(username)
        if user:
            return user.has_perm(*permissions)
        return False

    def get_user_by_id(self, user_id) -> User:
        return self.query(id=user_id).first()


class GroupService(BaseService):
    db = Group

    def __init__(self):
        self.default_group_name = 'Default'

    def get_group_by_name(self, name) -> Group:
        if isinstance(name, str):
            return self.query(name=name).first()
        return name

    def get_group_by_id(self, id) -> Group:
        if isinstance(id, str):
            return self.query(id=id).first()
        return id

    def create_group(self, name, permissions=None) -> Group:
        if permissions is None:
            permissions = []
        group = self.create(name=name)
        group.permissions.set(permissions)
        logger.info(f'创建用户组: {group}')
        return group

    def default_group(self):
        """
        创建默认用户组
        :return:
        """
        group = self.get_group_by_name(self.default_group_name)
        if not group:
            group = self.create_group(name=self.default_group_name)
        return group

    def add_user_to_group(self, *username: User | str, group_name: Group | str = None):
        """
        为用户设置所在组（高效批量）。

        通过一次性查询现有 `UserPrefile`，区分需要更新与新建的记录，分别使用
        `bulk_update` 与 `bulk_create`，显著减少 SQL 次数，确保“用户仅一个组”。

        :param username: 用户对象或用户名字符串，可变参数，支持批量
        :param group_name: 目标组对象或组名字符串；为空则加入默认组
        :returns: None
        """
        group_name = group_name or self.default_group_name
        group = self.get_group_by_name(group_name)
        if not group:
            group = self.default_group()

        user_service = UserService()
        user_objs: list[User] = []
        for item in username:
            if isinstance(item, User):
                user_objs.append(item)
            elif isinstance(item, str):
                if u := user_service.get_user_by_name(item):
                    user_objs.append(u)
            else:
                continue

        if not user_objs:
            return

        user_ids = [u.id for u in user_objs]

        with transaction.atomic():
            # 一次性读取已有的 Profile
            existing_profiles = UserPrefile.objects.filter(user_id__in=user_ids)
            user_id_to_profile = {p.user_id: p for p in existing_profiles}

            to_update: list[UserPrefile] = []
            to_create: list[UserPrefile] = []

            for u in user_objs:
                if u.id in user_id_to_profile:
                    profile = user_id_to_profile[u.id]
                    if profile.group_id != group.id:
                        profile.group = group
                        to_update.append(profile)
                else:
                    to_create.append(UserPrefile(user=u, group=group))

            if to_update:
                UserPrefile.objects.bulk_update(to_update, ['group'])
            if to_create:
                UserPrefile.objects.bulk_create(to_create)


class PermissionService(BaseService):
    db = Permission

    def get_permissions_list(self):
        return self.db.objects.all()

    def create_permission(self, content_type_id, name, codename) -> Permission:
        return self.create(
            content_type_id=content_type_id,
            name=name,
            codename=codename
        )

    def get_by_content_type_id(self, content_type_id) -> QuerySet[Permission]:
        return self.query(content_type_id=content_type_id).all()

    def get_by_codename(self, codename) -> QuerySet[Permission]:
        return self.query(codename=codename).all()

    def get_by_name(self, name) -> QuerySet[Permission]:
        return self.query(name=name).all()

    def get_permissions(self, *permission_name):
        return self.db.objects.filter(name__in=permission_name).all()


class SystemInfoService(BaseService):
    db = SystemInfo

    def get_client_info_by_uuid(self, uuid) -> SystemInfo:
        return self.query(uuid=uuid).first()

    def get_client_info_by_client_id(self, client_id) -> SystemInfo:
        return self.query(client_id=client_id).first()

    def update(self, uuid: str, **kwargs):
        """
        创建或更新系统信息
        
        :param uuid: 设备唯一标识
        :param kwargs: 系统信息字段
        :return: (created, object)元组
        """
        super().create_or_update(filters={
            'uuid': uuid,
        }, **kwargs)
        kwargs['uuid'] = uuid
        logger.info(f'更新设备信息: {kwargs}')

    def get_list(self, page=1, page_size=10):
        res = super().get_list(page=page, page_size=page_size)
        logger.debug(f'SystemInfo list: {res}')
        return res


class HeartBeatService(BaseService):
    db = HeartBeat

    def update(self, uuid, **kwargs):
        kwargs['modified_at'] = get_local_time()
        kwargs['timestamp'] = get_local_time()
        super().create_or_update(filters={'uuid': uuid}, **kwargs)
        # logger.debug(f'update heartbeat: {res}')
        # return res

    def is_alive(self, uuid, timeout=60):
        client = self.query(uuid=uuid).first()
        if client and get_local_time() - client.modified_at < timeout:
            return True
        return False

    def get_list(self, page=1, page_size=10, keep_alive_timeout=60):
        device_list = super().get_list(page=page, page_size=page_size)
        data = [
            {
                device.uuid: True if get_local_time() - device.modified_at < keep_alive_timeout else False
            } for device in device_list
        ]


class LoginClientService(BaseService):
    """
    登录客户端服务类

    用于处理登录客户端的相关业务逻辑
    """
    db = LoginClient

    def update_login_status(self, username, uuid, client_id):
        self.create_or_update(filters={
            'username': self.get_username(username),
            'uuid': self.get_uuid(uuid),
            'client_id': client_id,
        }, login_status=True)

        logger.info(f'更新登录状态: {username} - {uuid}')

    def update_logout_status(self, username, uuid, client_id):
        self.create_or_update(filters={
            'username': self.get_username(username),
            'uuid': self.get_uuid(uuid),
            'client_id': client_id,
        }, login_status=False)

        logger.info(f'更新登出状态: {username} - {uuid}')

    def get_login_client_list(self, username) -> QuerySet[LoginClient]:
        return self.query(username=self.get_username(username)).all()


class TokenService(BaseService):
    """
    令牌服务类

    用于处理令牌相关的业务逻辑
    """
    db = Token

    def create_token(self, username, uuid):
        username = username.username if isinstance(username, User) else username
        token = f'{get_randem_md5()}_{username}'
        self.create(
            username=self.get_username(username),
            uuid=self.get_uuid(uuid),
            token=token,
            created_at=get_local_time(),
            last_used_at=get_local_time(),
        )
        logger.info(f"创建令牌: user: {username} uuid: {uuid} token: {token}")
        return token

    def check_token(self, token, timeout=3600):
        if _token := self.query(token=token).first():
            return _token.last_used_at > get_local_time() - timedelta(seconds=timeout)
        self.delete(token=token)
        return False

    def update_token(self, token):
        if _token := self.query(token=token).first():
            _token.last_used_at = get_local_time()
            _token.save()
            return True
        return False

    def update_token_by_uuid(self, uuid):
        if _token := self.query(uuid=self.get_uuid(uuid)).first():
            _token.last_used_at = get_local_time()
            _token.save()
            logger.info(f"通过uuid更新令牌: {uuid} - {_token.token}")
            return True
        return False

    def delete_token(self, token):
        res = self.delete(token=token)
        logger.info(f"删除令牌: {token}")
        return res

    def delete_token_by_uuid(self, uuid):
        res = self.delete(uuid=self.get_uuid(uuid))
        logger.info(f"通过uuid删除令牌: {uuid}")
        return res

    def delete_token_by_user(self, username: User | str):
        if isinstance(username, User):
            username = username.username
        res = self.delete(username=username)
        logger.info(f"通过用户名删除令牌: {username}")
        return res

    # def get_user_info_by_token(self, token) -> User | None:
    #     if username := self.query(token=token).first().username:
    #         return UserService().get_user_by_name(username)
    #     return None

    @staticmethod
    def get_request_info(request: HttpRequest) -> tuple[str, User, dict]:
        authorization = request.headers.get('Authorization')[7:]
        username = authorization.split('_')[-1]
        body = json.loads(request.body) if request.body else {}
        return authorization, UserService().get_user_by_name(username), body

    def get_cur_uuid_by_token(self, token) -> str | None:
        if uuid := self.query(token=token).first().uuid:
            return uuid.uuid
        return None


class TagService:
    """
    标签服务类

    用于处理标签相关的业务逻辑
    """
    db_tag = Tag
    db_client = SystemInfo
    db_tag2client = TagToClient
    db_user2tag = UserToTag

    def __init__(self, username: User | str):
        self.username = UserService().get_username(username)

    def create_tag(self, tag, color, tag_type='user'):
        _tag, created = self.db_tag.objects.get_or_create(tag=tag, defaults={'color': color, 'tag_type': tag_type})
        if created:
            self.db_user2tag.objects.create(tag_id_id=_tag.id, username=self.username)

    def delete_tag(self, *tag):
        if self.username.is_superuser:
            self.db_tag.objects.filter(tag__in=tag).delete()
        else:
            self.db_tag.objects.filter(tag__in=tag, tag_type='user').delete()

    def update_tag(self, tag, color=None, new_tag=None):
        data = {}
        if color:
            data['color'] = color
        if new_tag:
            data['tag'] = new_tag
        return self.db_tag.objects.filter(tag=tag, tag_type='user').update(**data)

    def get_all_tags(self):
        """
        获取当前用户关联的所有标签

        :return: QuerySet of Tag objects associated with the current user
        """
        user_tags = self.username.usertotag_set.all()
        sys_tags = self.get_system_tags()
        tags = list(user_tags) + list(sys_tags)
        return list(set(tags))

    def get_system_tags(self):
        return self.db_tag.objects.filter(tag_type='system').all()

    def add_tag_to_client(self, tag, client_id):
        return self.db_tag2client.objects.get_or_create(tag=tag, client_id=client_id)

    def get_tag_client_list(self, tag):
        return self.db_tag2client.objects.filter(tag=tag)


class LogService(BaseService):
    """
    日志服务类

    用于处理日志相关的业务逻辑
    """
    db = Log

    def create_log(self, username, uuid, log_type, log_level='info', log_message=''):
        """
        创建日志记录

        :param username: 用户名
        :param uuid: 设备UUID
        :param log_type: 日志类型
        :param log_level: 日志级别
        :param log_message: 日志消息
        :return: 新创建的日志实例
        """
        log = self.create(
            username=self.get_username(username),
            uuid=self.get_uuid(uuid),
            log_level=log_level,
            operation_type=log_type,  # 根据实际需求映射到合适的操作类型
            operation_object='log',  # 根据实际需求设置操作对象
            operation_result='success',  # 假设日志创建总是成功的
            operation_detail=log_message,
            operation_time=get_local_time(),
        )
        logger.info(
            f"创建日志: 用户=\"{username}\", UUID=\"{uuid}\", 类型=\"{log_type}\", 级别=\"{log_level}\", 消息=\"{log_message}\"")
        return log


class AuditConnService(BaseService):
    """
    审计连接服务类

    用于处理审计连接相关的业务逻辑
    """
    db = AutidConnLog

    def get(self, conn_id, action='new') -> AutidConnLog:
        return self.query(conn_id=conn_id, action=action).first()

    def create_log(self, action, conn_id, initiating_ip, session_id, controlled_uuid, controller_uuid=None):
        """
        连接日志
        :param action:
        :param conn_id:
        :param initiating_ip:
        :param session_id:
        :param controller_uuid:
        :param controlled_uuid:
        :return:
        """
        if controller_uuid:
            controller_uuid = self.get_uuid(controller_uuid)
        controlled_uuid = self.get_uuid(controlled_uuid)

        data = {
            'action': action,
            'conn_id': conn_id,
            'session_id': session_id,
            'controller_uuid': controller_uuid,
            'controlled_uuid': controlled_uuid,
            'type': 0,
        }
        if initiating_ip:
            data['initiating_ip'] = initiating_ip

        log = self.create(**data)
        return log

    def update_log(self, conn_id, initiating_ip, session_id, controller_uuid, controlled_uuid, username='', _type=0):
        controller_uuid = self.get_uuid(controller_uuid)
        controlled_uuid = self.get_uuid(controlled_uuid)

        data = {
            'initiating_ip': initiating_ip,
            'session_id': session_id,
            'controller_uuid': controller_uuid,
            'controlled_uuid': controlled_uuid,
            'type': _type,
        }
        if username:
            data['username'] = self.get_username(username)

        return self.update(
            filters={
                'conn_id': conn_id,
            },
            **data,
        )
