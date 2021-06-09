import typing as t

import sqlalchemy as alchemy
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base, declared_attr
from sqlalchemy.sql.base import ImmutableColumnCollection

from src.others.casing import camel_to_snake


class CustomMeta(DeclarativeMeta):
    __table__: alchemy.Table

    @property
    def columns(cls) -> ImmutableColumnCollection:
        return cls.__table__.columns


class CustomBase:
    __table__: alchemy.Table

    if t.TYPE_CHECKING:
        __tablename__: str
    else:

        @declared_attr
        def __tablename__(self) -> str:
            return camel_to_snake(self.__name__)

    def dict(self) -> t.Dict[str, t.Any]:
        data = {key: getattr(self, key) for key in self.__table__.columns.keys()}
        return data


_Base = declarative_base(cls=CustomBase, metaclass=CustomMeta)

if t.TYPE_CHECKING:

    class Base(_Base, CustomBase, metaclass=CustomMeta):
        __table__: alchemy.Table
        __tablename_: str

        metadata: alchemy.MetaData
        columns: ImmutableColumnCollection


else:
    Base = _Base
