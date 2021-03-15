from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession

from .custom_db_base import Base


async def on_conflict(
    session: AsyncSession, model: Base, conflict_columns: list, values: dict
) -> None:
    table = model.__table__
    stmt = postgresql.insert(table)

    affected_columns = {
        col.name: col
        for col in stmt.excluded
        if col.name in values and col.name not in conflict_columns
    }

    if not affected_columns:
        raise ValueError("Couldn't find any columns to update.")

    stmt = stmt.on_conflict_do_update(
        index_elements=conflict_columns, set_=affected_columns
    )

    await session.execute(stmt, values)
