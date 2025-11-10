"""
Base classes para models do SQLAlchemy
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Classe base para todos os models"""

    pass


class TimestampMixin:
    """Mixin para adicionar timestamps automáticos"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class BaseModel(Base, TimestampMixin):
    """Model base com ID e timestamps"""

    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    def to_dict(self) -> dict[str, Any]:
        """Converte o model para dicionário"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def __repr__(self) -> str:
        """Representação string do model"""
        attrs = ", ".join(
            f"{k}={v!r}"
            for k, v in self.to_dict().items()
            if k not in ("created_at", "updated_at")
        )
        return f"{self.__class__.__name__}({attrs})"
