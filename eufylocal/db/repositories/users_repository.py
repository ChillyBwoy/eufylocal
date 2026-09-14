from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eufylocal.db.models import UserModel


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self) -> list[UserModel]:
        """Return all users ordered by name and ID."""
        stmt = select(UserModel).order_by(UserModel.name, UserModel.id)
        return list(await self.session.scalars(stmt))

    async def create(self, name: str, color: str) -> UserModel:
        """Create and return a user."""
        user = UserModel(name=name, color=color)
        self.session.add(user)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return user

    async def update(
        self,
        user_id: int,
        name: str | None,
        color: str | None,
    ) -> UserModel | None:
        """Update the provided fields and return the user if it exists."""
        user = await self.session.get(UserModel, user_id)
        if user is None:
            return None

        if name is not None:
            user.name = name
        if color is not None:
            user.color = color
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return user

    async def delete(self, user_id: int) -> bool:
        """Delete a user by ID and report whether it existed."""
        user = await self.session.get(UserModel, user_id)
        if user is None:
            return False

        await self.session.delete(user)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return True
