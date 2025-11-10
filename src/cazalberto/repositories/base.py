"""
Repository base com operações CRUD genéricas
"""

from typing import Any, Generic, TypeVar

from sqlalchemy import Select, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Repository base com operações CRUD"""

    def __init__(self, model: type[ModelType], session: AsyncSession):
        """
        Args:
            model: Classe do model SQLAlchemy
            session: Sessão do banco de dados
        """
        self.model = model
        self.session = session

    async def get(self, id: int) -> ModelType | None:
        """
        Busca um registro por ID

        Args:
            id: ID do registro

        Returns:
            Model ou None se não encontrado
        """
        return await self.session.get(self.model, id)

    async def get_all(
        self, skip: int = 0, limit: int = 100, order_by: Any = None
    ) -> list[ModelType]:
        """
        Lista todos os registros com paginação

        Args:
            skip: Quantos registros pular
            limit: Máximo de registros a retornar
            order_by: Campo para ordenação

        Returns:
            Lista de models
        """
        stmt: Select[tuple[ModelType]] = select(self.model).offset(skip).limit(limit)

        if order_by is not None:
            stmt = stmt.order_by(order_by)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> ModelType:
        """
        Cria um novo registro

        Args:
            **kwargs: Campos do model

        Returns:
            Model criado
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: int, **kwargs: Any) -> ModelType | None:
        """
        Atualiza um registro

        Args:
            id: ID do registro
            **kwargs: Campos a atualizar

        Returns:
            Model atualizado ou None se não encontrado
        """
        instance = await self.get(id)
        if instance is None:
            return None

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def delete(self, id: int) -> bool:
        """
        Remove um registro

        Args:
            id: ID do registro

        Returns:
            True se removido, False se não encontrado
        """
        instance = await self.get(id)
        if instance is None:
            return False

        await self.session.delete(instance)
        await self.session.commit()
        return True

    async def delete_many(self, **filters: Any) -> int:
        """
        Remove múltiplos registros que atendem aos filtros

        Args:
            **filters: Filtros para aplicar

        Returns:
            Número de registros removidos
        """
        stmt = delete(self.model)

        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)

        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount  # type: ignore

    async def count(self) -> int:
        """
        Conta o total de registros

        Returns:
            Número total de registros
        """
        from sqlalchemy import func

        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def exists(self, id: int) -> bool:
        """
        Verifica se um registro existe

        Args:
            id: ID do registro

        Returns:
            True se existe, False caso contrário
        """
        instance = await self.get(id)
        return instance is not None
