"""orm的基类和基本工具
"""
from typing import Type
from peewee import Proxy,Model
db = Proxy()
Tables = {}


class BaseModel(Model):
    class Meta:
        database = db


def register(clz: Type[BaseModel])->Type[BaseModel]:
    """用于将表注册进Tables的装饰器.

    便于统一管理所有的表

    Args:
        clz (Type[BaseModel]): 表类

    Raises:
        AttributeError: 如果注册的表不是BaseModel的子类则会抛出

    Returns:
        Type[BaseModel]: 返回实际的类
    """
    if not issubclass(clz, BaseModel):
        raise AttributeError("类型错误")
    Tables[clz.__name__] = clz
    return clz


__all__ = ["db", "Tables", "BaseModel", "register"]
