import logging
from datetime import timedelta
from typing import TypeVar

from django.contrib.auth.models import User
from django.db import models
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.common.utils import get_local_time, get_uuid
from apps.db.models import HeartBeat, SystemInfo, Token, LoginClient, TagToClient, Tag, UserToTag, Log

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

    def update(self, filters: dict, **kwargs):
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

    def create_user(self, username, password, email='', is_superuser=False, is_staff=False) -> User:
        user = self.create(
            username=username,
            email=email,
            is_superuser=is_superuser,
            is_staff=is_staff,
        )
        user.set_password(password)
        user.save()
        logger.info(f'创建用户: {user}')
        return user

    def get_user_by_email(self, email) -> User:
        return self.query(email=email).first()

    def get_user_by_name(self, username) -> User:
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

    def get_list(self, status, page=1, page_size=10):
        return super().get_list(
            filters={'is_active': status}, page=page, page_size=page_size
        )


class SystemInfoService(BaseService):
    db = SystemInfo

    def get_client_info_by_uuid(self, uuid) -> SystemInfo:
        return self.query(uuid=uuid).first()

    def update(self, uuid: str, **kwargs):
        """
        创建或更新系统信息
        
        :param uuid: 设备唯一标识
        :param kwargs: 系统信息字段
        :return: (created, object)元组
        """
        super().update(
            filters={
                'uuid': uuid,
            },
            **kwargs
        )
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
        res = super().update(filters={'uuid': uuid}, **kwargs)
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
        res = self.update(
            filters={
                'username': self.get_username(username),
                'uuid': self.get_uuid(uuid),
                'client_id': client_id,
            },
            login_status=True,
        )

        logger.info(f'更新登录状态: {username} - {uuid}')
        return res

    def update_logout_status(self, username, uuid, client_id):
        res = self.update(
            filters={
                'username': self.get_username(username),
                'uuid': self.get_uuid(uuid),
                'client_id': client_id,
            },
            login_status=False,
        )

        logger.info(f'更新登出状态: {username} - {uuid}')
        return res

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
        token = f'{get_uuid()}_{username}'
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

    # def get_user_info_by_token(self, token) -> User | None:
    #     if username := self.query(token=token).first().username:
    #         return UserService().get_user_by_name(username)
    #     return None

    @staticmethod
    def get_user_token(request: HttpRequest) -> tuple[str, User]:
        authorization = request.headers.get('Authorization')[7:]
        username = authorization.split('_')[-1]
        return authorization, UserService().get_user_by_name(username)

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

    def __init__(self, username):
        self.username = username

    def create_tag(self, tag, color):
        _tag, created = self.db_tag.objects.get_or_create(tag=tag, defaults={'color': color})
        if created:
            self.db_user2tag.objects.create(tag_id_id=_tag.id, username=self.username)

    def delete_tag(self, tag):
        self.db_tag.objects.filter(tag=tag)

    def update_tag(self, tag, color=None, new_tag=None):
        data = {}
        if color:
            data['color'] = color
        if new_tag:
            data['tag'] = new_tag
        return self.db_tag.objects.filter(tag=tag).update(**data)

    def get_all_tags(self):
        """
        获取当前用户关联的所有标签

        :return: QuerySet of Tag objects associated with the current user
        """
        user_tags = self.db_user2tag.objects.filter(username=self.username).select_related('tag_id')
        return [ut.tag_id for ut in user_tags]

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
