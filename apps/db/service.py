import ast
import json
import logging
from importlib import import_module
from typing import TypeVar

from django.conf import settings
from django.contrib.auth.models import User, Group, Permission
from django.contrib.sessions.backends.base import SessionBase
from django.contrib.sessions.models import Session
from django.db import models
from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest

from apps.db.models import (
    HeartBeat,
    PeerInfo,
    Token,
    LoginClient,
    Tag,
    Log,
    AutidConnLog,
    UserPrefile,
    Personal,
    Alias,
    ClientTags,
    SharePersonal,
)
from common.env import PublicConfig
from common.utils import get_local_time

logger = logging.getLogger(__name__)

# 定义泛型类型变量，用于表示各种模型类型
ModelType = TypeVar("ModelType", bound=models.Model)
SessionStore = import_module(settings.SESSION_ENGINE).SessionStore


class BaseService:
    """
    数据服务基类

    :param db: 需要操作的模型类
    """

    db: models.Model = None

    @staticmethod
    def get_user_info(username):
        if isinstance(username, str):
            username = UserService().get_user_by_name(username)
        return username

    @staticmethod
    def get_peer_by_uuid(uuid):
        if isinstance(uuid, str):
            uuid = PeerInfoService().get_peer_info_by_uuid(uuid)
        return uuid

    @staticmethod
    def get_peer_by_peer_id(peer_id):
        if isinstance(peer_id, str):
            peer_id = PeerInfoService().get_peer_info_by_peer_id(peer_id)
        return peer_id


class TokenService(BaseService):
    """
    令牌服务类

    用于处理令牌相关的业务逻辑
    """

    db = Token

    def __init__(self, request: HttpRequest | None = None):
        self.request = request
        self.default_timeout = PublicConfig.SESSION_TIMEOUT
        self.default_interval = PublicConfig.SESSION_INTERVAL

    @property
    def session(self):
        if session := self.request.session:
            return session
        return self.__get_session()

    def __get_session(self, sid=None) -> SessionBase:
        """

        :param sid:
        :return: SessionBase
        """
        if not sid:
            sid = self.authorization.split('_')[0]
        return SessionStore(session_key=sid)

    @staticmethod
    def check_session_key(sid):
        session_qs = Session.objects.filter(session_key=sid)
        if not session_qs.exists():
            return False
        return True

    @staticmethod
    def delete_session(*sid):
        Session.objects.filter(session_key__in=sid).delete()
        logger.debug(f"删除Django Session: {sid}")

    def __update_session_expiry(self, sid):
        self.__get_session(sid).set_expiry(self.default_timeout)
        logger.debug(f"更新 Django Session: {sid}")

    def create_token(self, username, uuid, sid):
        username = self.get_user_info(username)
        # token = f"{get_randem_md5()}_{username}"
        token = f"{sid}_{username}"
        self.db.objects.create(
            username=self.get_user_info(username),
            uuid=uuid,
            token=token,
            sid=sid,
            created_at=get_local_time(),
            last_used_at=get_local_time(),
        )
        logger.info(f"创建令牌: user: {username} uuid: {uuid} token: {token}")
        return token

    def check_token(self, token):
        sid = token.split('_')[0]
        if not self.check_session_key(sid):
            return False
        if self.session and self.session.get_expiry_age() < self.default_timeout:
            self.db.objects.filter(token=token).delete()
            return False
        return True

    def update_token(self, token):
        qs = self.db.objects.filter(token=token).first()
        if not qs:
            return False
        self.__update_session_expiry(qs.sid)
        return True

    def update_token_by_uuid(self, uuid):
        qs = self.db.objects.filter(uuid=uuid).first()
        if not qs:
            return False
        self.__update_session_expiry(qs.sid)
        return True

    def delete_token(self, token):
        qs = self.db.objects.filter(token=token).first()
        if qs:
            self.delete_session(qs.sid)
            logger.info(f"删除令牌: {token}")
        qs.delete()
        return qs

    def delete_token_by_user(self, username: User | str):
        if isinstance(username, User):
            username = username.username
        qs = self.db.objects.filter(username=username).all()
        self.delete_session(
            *[qs.sid for qs in qs]
        )
        qs.delete()
        logger.info(f"通过用户名删除令牌: {username}")
        return qs

    @property
    def authorization(self) -> str | None:
        if self.request:
            return self.request.headers.get("Authorization")[7:]
        return None

    @property
    def sid(self):
        return self.session.get('token') or self.authorization.split("_")[0]

    @property
    def username(self):
        return self.session.get('username') or self.authorization.split("_")[-1]

    @property
    def user_info(self) -> User | None:
        return UserService().get_user_by_name(self.username)

    @property
    def request_body(self) -> dict | list:
        if self.request:
            if body := self.request.body:
                return json.loads(body)
        return {}

    @property
    def request_query(self):
        if self.request:
            if params := self.request.GET:
                return params.dict()
        return {}

    def get_cur_uuid_by_token(self, token) -> str | None:
        if peer := self.db.objects.filter(token=token).first():
            return peer.uuid
        return None


class UserService(BaseService):
    db = User

    def get(self, email) -> User | None:
        try:
            return self.db.objects.get(email=email)
        except self.db.DoesNotExist:
            return None

    def get_users(self, *users):
        return self.db.objects.filter(username__in=[*users]).all()

    def create_user(
            self,
            username,
            password,
            email="",
            is_superuser=False,
            is_staff=False,
            group: str | Group = None,
    ) -> User:
        user = self.db.objects.create_user(
            username=username,
            email=email,
            is_superuser=is_superuser,
            is_staff=is_staff,
        )
        user.set_password(password)
        user.save()
        logger.info(f"创建用户: {user}")

        # 添加用户到组（确保参数顺序正确）
        group_service = GroupService()
        group_service.add_user_to_group(user, group_name=group)

        # 添加一个个人地址簿
        PersonalService().create_self_personal(user)

        return user

    def get_user_by_email(self, email) -> User:
        return self.db.objects.filter(email=email).first()

    def get_user_by_name(self, username) -> User:
        if isinstance(username, User):
            return username
        return self.db.objects.filter(username=username).first()

    def set_password(self, password, email=None, username=None):
        if username is not None:
            user = self.get_user_by_name(username)
        elif email is not None:
            user = self.get_user_by_email(email)
        else:
            raise ValueError("Either username or email must be provided.")
        if user is None:
            raise ValueError("User does not exist.")
        user.set_password(password)
        user.save()
        logger.info(f"设置用户密码: {user}")
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
        page = int(kwargs.pop("page", 1))
        page_size = int(kwargs.pop("page_size", 10))

        filters = kwargs.pop("filters", {})
        queryset = self.db.objects.filter(**filters)

        if ordering := kwargs.pop("ordering", []):
            queryset = queryset.order_by(*ordering)

        total = queryset.count()
        results = queryset[(page - 1) * page_size: page * page_size]

        return {
            "results": results,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    def get_list_by_status(self, status, page=1, page_size=10):
        return self.__get_list(status=status, page=page, page_size=page_size)

    def set_user_permissions(self, username, *permissions):
        permissions = self.db.objects.filter(
            user_permissions__codename__in=[*permissions]
        )
        user = self.get_user_by_name(username)
        if user:
            user.user_permissions.add(*permissions)

    def del_user_permissions(self, username, *permissions):
        permissions = self.db.objects.filter(
            user_permissions__codename__in=[*permissions]
        )

        user = self.get_user_by_name(username)
        if user:
            user.user_permissions.remove(*permissions)
            logger.info(f"删除用户权限: {user}")

    def get_user_permissions(self, username):
        user = self.get_user_by_name(username)
        if user:
            return user.user_permissions.all()
        return None

    def is_user_has_permission(self, username, *permissions) -> bool:
        permissions = self.db.objects.filter(
            user_permissions__codename__in=[*permissions]
        )
        user = self.get_user_by_name(username)
        if user:
            return user.has_perm(*permissions)
        return False

    def get_user_by_id(self, user_id) -> User:
        return self.db.objects.filter(id=user_id).first()


class GroupService(BaseService):
    db = Group

    def __init__(self):
        self.default_group_name = "Default"

    def get_group_by_name(self, name) -> Group:
        if isinstance(name, str):
            return self.db.objects.filter(name=name).first()
        return name

    def get_group_by_id(self, id) -> Group:
        if isinstance(id, str):
            return self.db.objects.filter(id=id).first()
        return id

    def create_group(self, name, permissions=None) -> Group:
        if permissions is None:
            permissions = []
        group = self.db.objects.create(name=name)
        group.permissions.add(*permissions)
        logger.info(f"创建用户组: {group}")
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
                UserPrefile.objects.bulk_update(to_update, ["group"])
                # logger.info(f"更新用户组: {to_update}")
            if to_create:
                UserPrefile.objects.bulk_create(to_create)
                # logger.info(f"创建用户组: {to_create}")
        return group


class PermissionService(BaseService):
    db = Permission

    def get_permissions_list(self):
        return self.db.objects.all()

    def create_permission(self, content_type_id, name, codename) -> Permission:
        perm = self.db.objects.create(
            content_type_id=content_type_id, name=name, codename=codename
        )
        logger.info(
            f"创建权限: content_type_id={content_type_id}, name={name}, codename={codename}"
        )
        return perm

    def get_by_content_type_id(self, content_type_id):
        return self.db.objects.filter(content_type_id=content_type_id).all()

    def get_by_codename(self, codename):
        return self.db.objects.filter(codename=codename).all()

    def get_by_name(self, name):
        return self.db.objects.filter(name=name).all()

    def get_permissions(self, *permission_name):
        return self.db.objects.filter(name__in=permission_name).all()


class PeerInfoService(BaseService):
    db = PeerInfo

    def get_peer_info_by_uuid(self, uuid):
        return self.db.objects.filter(uuid=uuid).first()

    def get_peer_info_by_peer_id(self, peer_id):
        return self.db.objects.filter(peer_id=peer_id).first()

    def update(self, uuid: str, **kwargs):
        """
        创建或更新系统信息

        :param uuid: 设备唯一标识
        :param kwargs: 系统信息字段
        :return: (created, object)元组
        """
        kwargs["uuid"] = uuid
        peer_id = kwargs.get("peer_id")

        if not self.db.objects.filter(Q(uuid=uuid) | Q(peer_id=peer_id)).update(**kwargs):
            self.db.objects.create(**kwargs)

        logger.info(f"更新设备信息: {kwargs}")

    def get_list(self):
        return self.db.objects.all()

    def get_peers(self, *peers):
        return self.db.objects.filter(peer_id__in=peers).all()


class HeartBeatService(BaseService):
    db = HeartBeat

    def update(self, uuid, **kwargs):
        """
        更新或创建心跳记录

        :param uuid: 设备UUID
        :param kwargs: 需要更新的字段，如 peer_id、ver 等
        :returns:
        """
        kwargs["modified_at"] = get_local_time()
        kwargs["timestamp"] = get_local_time()
        kwargs["uuid"] = uuid
        peer_id = kwargs.get("peer_id")

        if not self.db.objects.filter(Q(uuid=uuid) | Q(peer_id=peer_id)).update(**kwargs):
            self.db.objects.create(**kwargs)
        logger.info(f"更新心跳: {kwargs}")

    def is_alive(self, uuid, timeout=60):
        client = self.db.objects.filter(uuid=uuid).first()
        if client and get_local_time() - client.modified_at < timeout:
            return True
        return False


class LoginClientService(BaseService):
    """
    登录客户端服务类

    用于处理登录客户端的相关业务逻辑
    """

    db = LoginClient

    @property
    def platform(self):
        return {
            'windows': 1,
            'macos': 2,
            'linux': 3,
            'android': 4,
            'ios': 5,
            'web': 6,
        }

    @staticmethod
    def client_type(client_type: str):
        _type = 1 if client_type.lower() == 'web' else 2
        return _type

    def update_login_status(self, username, uuid, platform, client_type, client_name, peer_id=None):
        if not self.db.objects.filter(username=username, uuid=uuid).update(
                username=self.get_user_info(username),
                uuid=uuid,
                peer_id=peer_id,
                login_status=True,
                client_type=self.client_type(client_type),
                platform=self.platform[platform],
                client_name=client_name,
        ):
            self.db.objects.create(
                username=self.get_user_info(username),
                uuid=uuid,
                peer_id=peer_id,
                login_status=True,
                client_type=client_type,
                platform=platform,
                client_name=client_name,
            )

        logger.info(f"更新登录状态: {username} - {uuid}")

    def update_logout_status(self, username, uuid, peer_id=None):
        if not self.db.objects.filter(username=username, uuid=uuid).update(
                username=self.get_user_info(username),
                uuid=uuid,
                peer_id=peer_id,
                login_status=False,
        ):
            login_sq = self.db.objects.filter(
                username=self.get_user_info(username),
                uuid=uuid,
                login_status=True
            ).first()
            self.db.objects.create(
                username=self.get_user_info(username),
                uuid=uuid,
                peer_id=peer_id,
                login_status=False,
                client_type=login_sq.client_type,
                platform=login_sq.platform,
                client_name=login_sq.client_name,
            )

        logger.info(f"更新登出状态: {username} - {uuid}")

    def get_login_client_list(self, username):
        return self.db.objects.filter(username=self.get_user_info(username)).all()


class TagService:
    """
    标签服务类

    用于处理标签相关的业务逻辑
    """

    db_tag = Tag
    db_client = PeerInfo
    db_client_tags = ClientTags

    def __init__(self, guid, user: User | str):
        self.guid = guid
        self.user = UserService().get_user_info(user)

    def get_tags_by_name(self, *tag_name):
        res = self.db_tag.objects.filter(tag__in=tag_name, guid=self.guid).all()
        logger.debug(f"获取用户标签: {self.guid} - {tag_name} - {res}")
        return res

    def get_tags_by_id(self, *tag_id):
        return self.db_tag.objects.filter(id__in=tag_id, guid=self.guid).all()

    def create_tag(self, tag, color):
        res = self.db_tag.objects.create(tag=tag, color=color, guid=self.guid)
        logger.info(f"创建标签: {self.guid} - {tag} - {color}")
        return res

    def delete_tag(self, *tag):
        """
        删除指定标签，并在关系表中移除这些标签（单次批量更新）。

        :param str tag: 一个或多个需要删除的标签名
        """
        tags_to_delete = {str(t) for t in tag if t is not None}
        if not tags_to_delete:
            return

        # 遍历一次构造需要更新的实例，最后单次 bulk_update
        changed_instances = []
        for inst in self.db_client_tags.objects.filter(guid=self.guid).all():
            current_tags = self._parse_tags(inst.tags)
            if not current_tags:
                continue
            new_tags = [t for t in current_tags if t not in tags_to_delete]
            if new_tags != current_tags:
                # 统一以 JSON 格式写回
                inst.tags = json.dumps(new_tags)
                changed_instances.append(inst)

        if changed_instances:
            self.db_client_tags.objects.bulk_update(changed_instances, ["tags"])

        # 删除标签本身
        self.db_tag.objects.filter(tag__in=tags_to_delete, guid=self.guid).delete()
        logger.info(f"删除标签: {self.guid} - {tags_to_delete}")

    def update_tag(self, tag, color=None, new_tag=None):
        data = {}
        if color:
            data["color"] = color
        if new_tag:
            data["tag"] = new_tag
        res = self.db_tag.objects.filter(tag=tag, guid=self.guid).update(**data)
        logger.info(f"更新标签: {self.guid} - {data}")
        return res

    def get_all_tags(self):
        """
        获取当前用户关联的所有标签

        :return: QuerySet of Tag objects associated with the current user
        """
        return self.db_tag.objects.filter(guid=self.guid).all()

    def set_user_tag_by_peer_id(self, peer_id, tags):
        """
        为指定设备设置标签（覆盖式）。

        :param peer_id: 设备 peer_id
        :param tags: 标签列表
        :returns: 更新或创建的记录
        """
        tag_list = []
        for tag in self.get_tags_by_name(*list(tags)):
            tag_list.append(tag.id)

        # if qs := self.db_client_tags.objects.filter(peer_id=peer_id, guid=self.guid).first():
        if qs := self.user.user_tags.filter(peer_id=peer_id, guid=self.guid).first():
            qs.tags = str(tag_list if tag_list else [])
            return qs.save()

        kwargs = {
            "peer_id": peer_id,
            "tags": str(tag_list),
            "guid": self.guid,
        }
        res = self.user.user_tags.create(**kwargs)
        logger.info(f"设置标签: {self.guid} - {peer_id} - {tag_list if tag_list else []}")
        return res

    def del_tag_by_peer_id(self, *peer_id):
        """
        删除指定设备的标签记录。

        :param peer_id: 一个或多个设备的 peer_id
        :returns: 删除操作返回的 (rows_deleted, details)
        """
        res = self.user.user_tags.filter(peer_id__in=peer_id, guid=self.guid).delete()
        logger.info(f"删除标签: {self.guid} - {peer_id}")
        return res

    def get_tags_by_peer_id(self, peer_id) -> list[str]:
        """
        获取单个设备的标签列表。

        :param peer_id: 设备 peer_id
        :returns: 标签字符串列表，若无记录返回空列表
        """
        row = self.user.user_tags.filter(peer_id=peer_id, guid=self.guid).values("tags").first()
        if not row:
            return []
        return self._parse_tags(row.get("tags"))

    def get_tags_map(self, peer_ids: list[str]) -> dict[str, list[str]]:
        """
        批量获取多个设备的标签映射，避免 N+1 查询。

        :param peer_ids: 设备 `peer_id` 列表
        :returns: {peer_id: [tag, ...]} 映射
        """
        if not peer_ids:
            return {}
        rows = self.db_client_tags.objects.filter(guid=self.guid, peer_id__in=peer_ids).values("peer_id", "tags")
        logger.debug(f"批量获取标签: {self.guid} peers: {peer_ids} result: {rows}")
        result: dict[str, list[str]] = {}
        for row in rows:
            tags = eval(row.get("tags") or '[]')
            tags_qs = self.get_tags_by_id(*tags)
            logger.debug(f"标签: {self.guid} peers: {row['peer_id']} tags: {tags} result: {tags_qs}")
            if not tags_qs:
                continue
            result[row["peer_id"]] = [str(tag.tag) for tag in tags_qs]
        logger.debug(f"批量获取标签结果: guid: {self.guid} peers: {peer_ids} result: {result}")
        return result

    @staticmethod
    def _parse_tags(raw) -> list[str]:
        """
        解析存储在数据库中的标签字段。

        兼容 list 序列化为字符串的存储方式和 JSON 字符串。

        :param raw: 原始存储值（字符串或列表）
        :returns: 标签字符串列表
        """
        if raw is None:
            return []
        if isinstance(raw, list):
            return [str(x) for x in raw]
        s = str(raw).strip()
        if not s:
            return []
        # 优先尝试 JSON
        try:
            val = json.loads(s)
            if isinstance(val, list):
                return [str(x) for x in val]
        except Exception:
            pass
        # 回退到安全的字面量解析
        try:
            val = ast.literal_eval(s)
            if isinstance(val, list):
                return [str(x) for x in val]
        except Exception:
            pass
        return []


class LogService(BaseService):
    """
    日志服务类

    用于处理日志相关的业务逻辑
    """

    db = Log

    def create_log(self, username, uuid, log_type, log_level="info", log_message=""):
        """
        创建日志记录

        :param username: 用户名
        :param uuid: 设备UUID
        :param log_type: 日志类型
        :param log_level: 日志级别
        :param log_message: 日志消息
        :return: 新创建的日志实例
        """
        log = self.db.objects.create(
            username=self.get_user_info(username),
            uuid=self.get_peer_by_uuid(uuid),
            log_level=log_level,
            operation_type=log_type,  # 根据实际需求映射到合适的操作类型
            operation_object="log",  # 根据实际需求设置操作对象
            operation_result="success",  # 假设日志创建总是成功的
            operation_detail=log_message,
            operation_time=get_local_time(),
        )
        logger.info(
            f'创建日志: 用户="{username}", UUID="{uuid}", 类型="{log_type}", 级别="{log_level}", 消息="{log_message}"'
        )
        return log


class AuditConnService(BaseService):
    """
    审计连接服务类

    用于处理审计连接相关的业务逻辑
    """

    db = AutidConnLog

    def get(self, conn_id, action="new") -> AutidConnLog:
        return self.db.objects.filter(conn_id=conn_id, action=action).first()

    def log(
            self,
            conn_id,
            action,
            controlled_uuid,
            source_ip,
            session_id,
            controller_peer_id=None,
            type_=0,
            username=None
    ):
        """
        记录日志
        :param username:
        :param type_:
        :param controller_peer_id:
        :param conn_id:
        :param action:
        :param controlled_uuid:
        :param source_ip:
        :param session_id:
        :return:
        """
        if action:
            if action == "new":
                self.db.objects.create(
                    conn_id=conn_id,
                    action=action,
                    controlled_uuid=self.get_peer_by_uuid(controlled_uuid),
                    initiating_ip=source_ip,
                    session_id=session_id,
                )
            else:
                connect_log = self.db.objects.filter(
                    conn_id=conn_id,
                    action="new",
                ).first()
                self.db.objects.create(
                    conn_id=conn_id,
                    action=action,
                    controlled_uuid=self.get_peer_by_uuid(controlled_uuid),
                    controller_uuid=connect_log.controlled_uuid,
                    initiating_ip=connect_log.initiating_ip,
                    session_id=session_id,
                    username=connect_log.username,
                    type=connect_log.type,
                )
        else:
            self.db.objects.filter(conn_id=conn_id).update(
                session_id=session_id,
                controller_uuid=self.get_peer_by_peer_id(controller_peer_id),
                username=self.get_user_info(username),
                type=type_,
            )
        logger.info(
            f'审计连接: conn_id="{conn_id}", action="{action}", controlled_uuid="{controlled_uuid}", source_ip="{source_ip}", session_id="{session_id}"'
        )


class PersonalService(BaseService):
    db = Personal

    def create_personal(self, personal_name, create_user, personal_type="public"):
        create_user = self.get_user_info(create_user)
        personal = self.db.objects.create(
            personal_name=personal_name,
            create_user=create_user,
            personal_type=personal_type,
        )
        personal.personal_user.create(user=create_user)
        logger.info(
            f'创建地址簿: name: {personal_name}, create_user: {create_user}, type: {personal_type}, guid: {personal.guid}'
        )
        return personal

    def create_self_personal(self, username):
        username = self.get_user_info(username)
        personal = self.create_personal(
            personal_name=f'{username.username}_personal',
            create_user=username,
            personal_type="private"
        )
        logger.info(f'创建个人地址簿: user: {username}, personal_name: {personal.personal_name}, guid: {personal.guid}')
        return personal

    def get_personal(self, guid):
        return self.db.objects.filter(guid=guid).first()

    def get_all_personal(self):
        return self.db.objects.all()

    def delete_personal(self, guid):
        personal = self.get_personal(guid=guid)
        if personal and personal.personal_type != "private":
            logger.info(f'删除地址簿: {personal.personal_name} - {personal.personal_name}')
            return personal.delete()
        logger.info(f'无地址簿信息: {guid}')
        return None

    def add_personal_to_user(self, guid, username):
        user = self.get_user_info(username)
        res = self.get_personal(guid=guid).personal_user.create(username=user)
        logger.info(f'分享地址簿给用户: {guid} - {username}')
        return res

    def del_personal_to_user(self, guid, username):
        username = self.get_user_info(username)
        res = (
            self.get_personal(guid=guid)
            .personal_user.filter(username=username)
            .delete()
        )
        logger.info(f'取消分享地址簿: guid={guid}, username={username}')
        return res

    def add_peer_to_personal(self, guid, peer_id):
        peer = PeerInfoService().get_peer_info_by_peer_id(peer_id)
        return self.get_personal(guid=guid).personal_peer.create(peer=peer)

    def del_peer_to_personal(self, guid, peer_id: list | str, user):
        if isinstance(peer_id, str):
            peer_id = [peer_id]
        peers = PeerInfoService().get_peers(*peer_id)

        # 清掉alias
        alias_service = AliasService()
        for peer in peers:
            alias_service.set_alias(peer_id=peer.peer_id, guid=guid, alias="")

        # 清掉tag
        tag_service = TagService(guid=guid, user=user)
        tag_service.del_tag_by_peer_id(*peer_id)
        res = self.get_personal(guid=guid).personal_peer.filter(peer__in=peers).delete()
        logger.info(f'从地址簿移除设备: guid={guid}, peer_ids={peer_id}')
        return res


class AliasService(BaseService):
    db = Alias

    def set_alias(self, peer_id, alias, guid):
        """
        设置或更新某地址簿下设备的别名。

        :param str peer_id: 设备的 `peer_id`
        :param str alias: 要设置的别名
        :param str guid: 地址簿 GUID
        :returns: None
        """
        # 注意：模型字段 `peer_id` 与 `guid` 均为 ForeignKey；
        # 若直接赋字符串会被认为是传入关联对象，需使用 `<field>_id` 列名进行原值写入
        kwargs = {
            "peer_id_id": peer_id,
            "guid_id": guid,
            "alias": alias,
        }
        updated = self.db.objects.filter(peer_id_id=peer_id, guid_id=guid).update(**kwargs)
        if not updated:
            self.db.objects.create(**kwargs)
        logger.info(f'设置别名: peer_id="{peer_id}", alias="{alias}", guid="{guid}"')

    def get_alias(self, guid):
        return self.db.objects.filter(guid=guid).all()

    def get_alias_map(self, guid: str, peer_ids: list[str]) -> dict[str, str]:
        """
        批量获取某地址簿下多个设备的别名映射。

        :param guid: 地址簿 GUID
        :param peer_ids: 设备 `peer_id` 列表
        :returns: {peer_id: alias} 映射字典，未设置别名的设备不会出现在字典中
        """
        if not peer_ids:
            return {}
        rows = self.db.objects.filter(guid=guid, peer_id__in=peer_ids).values("peer_id", "alias")
        return {row["peer_id"]: row["alias"] for row in rows}


class SharePersonalService(BaseService):
    db = SharePersonal

    def __init__(self, count_user: User):
        self.user = count_user

    def share_to_user(self, guid, username):
        user = PersonalService().get_user_info(username)
        return self.db.objects.create(
            guid=guid,
            to_share_id=user.id,
            to_share_type=1,
            from_share_id=self.user.id,
            from_share_type=1,
        )

    def share_to_group(self, guid, group_name):
        group = GroupService().get_group_by_name(group_name)
        return self.db.objects.create(
            guid=guid,
            to_share_id=group.id,
            to_share_type=2,
            from_share_id=self.user.id,
            from_share_type=1,
        )

    def get_user_personals(self):
        group_id = self.user.userprofile.group_id
        personal_ids = self.db.objects.filter(
            to_share_id__in=(self.user.id, group_id),
            to_share_type__in=(1, 2),
        ).values_list("guid", flat=True)

        return PersonalService.db.objects.filter(guid__in=personal_ids).all()
