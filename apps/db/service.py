import logging
import time
from datetime import datetime, timedelta
from uuid import uuid5, NAMESPACE_DNS

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.utils import timezone

from django.db import models

from apps.db.models import HeartBeat, SystemInfo, LoginLog, Token

logger = logging.getLogger(__name__)


class BaseService:
    """
    数据服务基类
    
    :param db: 需要操作的模型类
    """
    db: models.Model = None

    def get_list(self, filters=None, ordering=None, page=1, page_size=10):
        """
        通用分页查询方法
        
        :param filters: 查询条件字典
        :param ordering: 排序字段列表
        :param page: 当前页码
        :param page_size: 每页记录数
        :return: 包含分页信息的字典
        """
        filters = filters or {}
        queryset = self.db.objects.filter(**filters)

        if ordering:
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

    def create(self, **kwargs):
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

    def query(self, *args, **kwargs):
        """
        通用条件查询
        
        :param args: Q查询对象
        :param kwargs: 查询条件
        :return: 查询结果集合
        """
        return self.db.objects.filter(*args, **kwargs)

    def query_all(self, *args, **kwargs):
        """
        获取全部匹配记录
        
        :param args: Q查询对象
        :param kwargs: 查询条件
        :return: 全部查询结果
        """
        return self.query(*args, **kwargs).all()

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


class UserService(BaseService):
    db = User

    def get(self, email):
        try:
            return self.db.objects.get(email=email)
        except self.db.DoesNotExist:
            return None

    def create_user(self, user_name, password, email='', is_superuser=False, is_staff=False):
        return self.create(
            username=user_name,
            password=password,
            email=email,
            is_superuser=is_superuser,
            is_staff=is_staff
        )

    def get_user_by_email(self, email):
        return self.query(email=email).first()

    def get_user_by_name(self, user_name):
        return self.query(username=user_name).first()

    def set_password(self, password, email=None, user_name=None):
        if user_name is not None:
            user = self.get_user_by_name(user_name)
        elif email is not None:
            user = self.get_user_by_email(email)
        else:
            raise ValueError("Either user_name or email must be provided.")
        user.set_password(password)
        user.save()


class SystemInfoService(BaseService):
    db = SystemInfo

    def update(self, uuid: str, **kwargs):
        """
        创建或更新系统信息
        
        :param uuid: 设备唯一标识
        :param kwargs: 系统信息字段
        :return: (created, object)元组
        """
        return super().update(
            filters={
                'uuid': uuid,
            },
            **kwargs
        )


class HeartBeatService(BaseService):
    db = HeartBeat

    def update(self, uuid, **kwargs):
        # 处理时间戳转datetime
        if 'modified_at' in kwargs:
            try:
                if isinstance(kwargs['modified_at'], (int, float)):
                    naive_dt = datetime.fromtimestamp(kwargs['modified_at'])
                    kwargs['modified_at'] = timezone.make_aware(naive_dt)
                elif isinstance(kwargs['modified_at'], str):
                    naive_dt = datetime.fromisoformat(kwargs['modified_at'])
                    kwargs['modified_at'] = timezone.make_aware(naive_dt)
            except Exception as e:
                logger.error(f'Datetime conversion error: {e}')
                raise ValueError("Invalid modified_at format") from e
        else:
            # 如果没有提供 modified_at，则使用当前时间
            current_time = timezone.now()
            kwargs['modified_at'] = current_time

        # timestamp 字段始终使用当前时间
        kwargs['timestamp'] = timezone.now()

        return super().update(filters={'uuid': uuid}, **kwargs)

    def is_alive(self, uuid):
        client = self.query(uuid=uuid).first()
        # client_time = client. if client else None


class LoginLogService(BaseService):
    """
    登录日志服务类

    用于处理登录日志的相关业务逻辑
    """
    db = LoginLog

    def create(self, **kwargs):
        """
        创建登录日志记录

        :param kwargs: 登录日志的字段值
        :return: 创建的登录日志对象
        """
        # 从 deviceInfo 中提取设备信息
        device_info = kwargs.pop('deviceInfo', {})
        if device_info:
            kwargs['os'] = device_info.get('os', '')
            kwargs['device_type'] = device_info.get('type', '')
            kwargs['device_name'] = device_info.get('name', '')

        # 处理字段名映射
        if 'id' in kwargs:
            kwargs['client_id'] = kwargs.pop('id')
        if 'type' in kwargs:
            kwargs['login_type'] = kwargs.pop('type')
        if 'autoLogin' in kwargs:
            kwargs['auto_login'] = kwargs.pop('autoLogin')

        return super().create(**kwargs)


class TokenService(BaseService):
    """
    令牌服务类

    用于处理令牌相关的业务逻辑
    """
    db = Token

    def create_token(self, username, uuid):
        token = uuid5(NAMESPACE_DNS, username + uuid + str(time.time()))
        self.create(
            username=username,
            uuid=uuid,
            token=token,
            created_at=timezone.now(),
            last_used_at=timezone.now(),
        )
        return token

    def check_token(self, token, timeout=3600):
        if _token := self.query(token=token).first():
            return _token.last_used_at > timezone.now() - timedelta(seconds=timeout)
        return False

    def update_token(self, token):
        if _token := self.query(token=token).first():
            _token.last_used_at = timezone.now()
            _token.save()
            return Token
        return False

    def delete_token_by_uuid(self, uuid):
        return self.delete(uuid=uuid)


user_service = UserService()
if not user_service.get_user_by_name('admin'):
    user_service.create_user(
        user_name='admin',
        password=make_password('admin'),
        email='',
        is_superuser=True,
        is_staff=True
    )
