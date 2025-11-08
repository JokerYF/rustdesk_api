from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterable, Optional, TypeVar

from django.db import models
from django.db.models import Model, ForeignKey
from django.db.models.fields.files import FieldFile
from django.utils.dateparse import parse_date, parse_datetime, parse_time

# 定义泛型类型变量，用于表示各种模型类型
ModelType = TypeVar("ModelType", bound=models.Model)


class ModelToDictMixin:
    """
    通用的 Django 模型字典化混入类。

    该混入类提供对模型实例进行可配置序列化为 `dict` 的能力，支持字段筛选、外键与多对多关系处理、
    深度嵌套、常见类型安全序列化（日期/时间、Decimal、文件字段）。
    """

    def to_dict(
            self,
            *,
            fields: Optional[Iterable[str]] = None,
            exclude: Optional[Iterable[str]] = None,
            include_fk: bool = True,
            include_m2m: bool = False,
            depth: int = 0,
            date_fmt: Optional[str] = None,
    ) -> dict:
        """
        将模型实例序列化为字典。

        :param fields: 仅包含的字段名集合，为 ``None`` 表示包含全部字段
        :type fields: Optional[Iterable[str]]
        :param exclude: 需要排除的字段名集合
        :type exclude: Optional[Iterable[str]]
        :param include_fk: 是否以 ``<field>_id`` 的形式输出外键主键；当为 ``False`` 时将按 ``depth`` 处理
        :type include_fk: bool
        :param include_m2m: 是否包含多对多字段
        :type include_m2m: bool
        :param depth: 关联对象嵌套深度，``> 0`` 时可递归调用关联对象的 ``to_dict``
        :type depth: int
        :param date_fmt: 日期/时间格式化字符串；为 ``None`` 时使用 ISO 8601
        :type date_fmt: Optional[str]
        :returns: 可 JSON 序列化的字典
        :rtype: dict
        """

        allowed: Optional[set[str]] = set(fields) if fields is not None else None
        excluded: set[str] = set(exclude) if exclude is not None else set()

        def allowed_field(name: str) -> bool:
            if name in excluded:
                return False
            if allowed is not None and name not in allowed:
                return False
            return True

        def serialize_scalar(value: Any) -> Any:
            if value is None:
                return None
            if isinstance(value, (datetime, date)):
                return value.strftime(date_fmt) if date_fmt else value.isoformat()
            if isinstance(value, Decimal):
                # 用字符串避免精度丢失；如需浮点可改为 float(value)
                return str(value)
            if isinstance(value, FieldFile):
                if not value:
                    return None
                # 优先返回可访问的 url，否则返回文件名
                return getattr(value, "url", None) or value.name
            if isinstance(value, Model):
                return getattr(value, "pk", None)
            return value

        data: dict[str, Any] = {"pk": getattr(self, "pk", None)}

        # 处理具体字段（含外键）
        for field in self._meta.concrete_fields:
            if isinstance(field, ForeignKey):
                # 外键字段名，例如 user；id 字段名为 user_id
                if include_fk and depth <= 0:
                    name = field.attname  # user_id
                    if allowed_field(name):
                        data[name] = serialize_scalar(getattr(self, field.attname))
                else:
                    name = field.name  # user
                    if allowed_field(name):
                        related_obj = getattr(self, name)
                        if related_obj is None:
                            data[name] = None
                        else:
                            if depth > 0 and hasattr(related_obj, "to_dict"):
                                data[name] = related_obj.to_dict(
                                    fields=None,
                                    exclude=None,
                                    include_fk=True,
                                    include_m2m=False,
                                    depth=depth - 1,
                                    date_fmt=date_fmt,
                                )
                            else:
                                data[name] = serialize_scalar(related_obj)
            else:
                name = field.name
                if allowed_field(name):
                    data[name] = serialize_scalar(getattr(self, name))

        # 处理多对多
        if include_m2m:
            for m2m_field in self._meta.many_to_many:
                name = m2m_field.name
                if not allowed_field(name):
                    continue
                manager = getattr(self, name)
                if depth > 0:
                    items: list[Any] = []
                    for obj in manager.all():
                        if hasattr(obj, "to_dict"):
                            items.append(
                                obj.to_dict(
                                    include_fk=True,
                                    include_m2m=False,
                                    depth=depth - 1,
                                    date_fmt=date_fmt,
                                )
                            )
                        else:
                            items.append(serialize_scalar(obj))
                    data[name] = items
                else:
                    data[name] = list(manager.values_list("pk", flat=True))

        return data


def update_model_from_dict(
        instance: Model,
        data: dict,
        *,
        save: bool = True,
        using: Optional[str] = None,
        clean: bool = True,
        ignore_unknown: bool = True,
        clear_m2m: bool = False,
        date_fmt: Optional[str] = None,
) -> ModelType:
    """
    将字典/JSON 数据应用到已存在的模型实例上。

    :param instance: 目标模型实例
    :type instance: Model
    :param data: 字段名到值的映射；外键支持 ``<field>`` 或 ``<field>_id``；多对多支持主键列表
    :type data: dict
    :param save: 是否在赋值后立即保存实例
    :type save: bool
    :param using: 指定使用的数据库别名
    :type using: Optional[str]
    :param clean: 保存前是否调用 ``full_clean()`` 做字段校验
    :type clean: bool
    :param ignore_unknown: 是否忽略未知字段（未知时跳过而不报错）
    :type ignore_unknown: bool
    :param clear_m2m: 当提供空列表时是否清空多对多关系
    :type clear_m2m: bool
    :param date_fmt: 当值为字符串且非 ISO 格式时的日期解析提示（留作扩展）
    :type date_fmt: Optional[str]
    :returns: 更新后的实例
    :rtype: Model
    """

    opts = instance._meta
    pending_m2m: dict[str, list[Any]] = {}

    def coerce_bool(v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if v is None:
            return False
        s = str(v).strip().lower()
        return s in {"1", "true", "t", "yes", "y"}

    def parse_for_field(field: models.Field, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(field, models.DateTimeField):
            if isinstance(value, datetime):
                return value
            if isinstance(value, str):
                v = value.replace("Z", "+00:00")
                dt = parse_datetime(v)
                return dt
            return value
        if isinstance(field, models.DateField):
            if isinstance(value, date):
                return value
            if isinstance(value, str):
                return parse_date(value)
            return value
        if isinstance(field, models.TimeField):
            if isinstance(value, str):
                return parse_time(value)
            return value
        if isinstance(field, models.DecimalField):
            if isinstance(value, Decimal):
                return value
            return Decimal(str(value))
        if isinstance(field, models.BooleanField):
            return coerce_bool(value)
        if isinstance(field, models.FileField):
            if isinstance(value, str):
                return value
            return value
        return value

    # 先处理非 M2M 字段
    for key, raw_value in (data or {}).items():
        try:
            field = opts.get_field(key)
            name = field.name
        except Exception:
            # 兼容 <fk>_id 直接赋值
            if key.endswith("_id"):
                base = key[:-3]
                try:
                    fk_field = opts.get_field(base)
                    if isinstance(fk_field, models.ForeignKey):
                        setattr(instance, key, raw_value)
                        continue
                except Exception:
                    pass
            if not ignore_unknown:
                raise
            continue

        # 多对多延后设置
        if isinstance(field, models.ManyToManyField):
            if raw_value is None:
                continue
            if isinstance(raw_value, (list, tuple)):
                pending_m2m[name] = list(raw_value)
            elif clear_m2m and raw_value == []:
                pending_m2m[name] = []
            else:
                pending_m2m[name] = [raw_value]
            continue

        # 外键：接受 pk 或 dict
        if isinstance(field, models.ForeignKey):
            if raw_value is None:
                setattr(instance, field.attname, None)
            elif isinstance(raw_value, dict):
                target_pk = (
                        raw_value.get("pk")
                        or raw_value.get("id")
                        or raw_value.get(field.target_field.attname)
                )
                setattr(instance, field.attname, target_pk)
            else:
                setattr(instance, field.attname, raw_value)
            continue

        # 常规字段
        if not getattr(field, "editable", True):
            continue
        value = parse_for_field(field, raw_value)
        setattr(instance, field.attname if hasattr(field, "attname") else field.name, value)

    # 保存本体，确保有 pk 可写入 M2M
    if save:
        if clean:
            instance.full_clean()
        instance.save(using=using)

    # 设置多对多（需在保存之后）
    for m2m_name, items in pending_m2m.items():
        manager = getattr(instance, m2m_name)
        # 统一为主键列表
        pks: list[Any] = []
        for item in items:
            if isinstance(item, dict):
                pk = item.get("pk") or item.get("id")
                if pk is not None:
                    pks.append(pk)
            else:
                pks.append(item)
        if pks or clear_m2m:
            manager.set(pks)

    return instance


def model_from_dict(
        model_cls: type[Model],
        data: dict,
        *,
        save: bool = True,
        using: Optional[str] = None,
        clean: bool = True,
        ignore_unknown: bool = True,
        date_fmt: Optional[str] = None,
) -> ModelType:
    """
    根据给定字典/JSON 创建并返回模型实例。

    :param model_cls: 目标模型类
    :type model_cls: Type[Model]
    :param data: 字段名到值的映射；外键支持 ``<field>`` 或 ``<field>_id``；多对多支持主键列表
    :type data: dict
    :param save: 是否在赋值后立即保存实例
    :type save: bool
    :param using: 指定使用的数据库别名
    :type using: Optional[str]
    :param clean: 保存前是否调用 ``full_clean()`` 做字段校验
    :type clean: bool
    :param ignore_unknown: 是否忽略未知字段（未知时跳过而不报错）
    :type ignore_unknown: bool
    :param date_fmt: 当值为字符串且非 ISO 格式时的日期解析提示（留作扩展）
    :type date_fmt: Optional[str]
    :returns: 新创建的实例
    :rtype: Model
    """

    instance = model_cls()
    return update_model_from_dict(
        instance,
        data,
        save=save,
        using=using,
        clean=clean,
        ignore_unknown=ignore_unknown,
        clear_m2m=False,
        date_fmt=date_fmt,
    )


# 简短别名：便于在调用处语义更贴近“JSON→Model”
json_to_model = model_from_dict
apply_json_to_model = update_model_from_dict
