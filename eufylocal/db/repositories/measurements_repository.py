from datetime import UTC, datetime

from sqlalchemy import ColumnExpressionArgument, ScalarSelect, case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from eufylocal.db.exceptions import DbEntityNotFoundError
from eufylocal.db.models import MeasurementModel, UserModel
from eufylocal.schemas.measurement import MeasurementUnit

DEFAULT_WEIGHT_THRESHOLD_PERCENT = 7.0


class MeasurementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert(
        self,
        weight: float,
        unit: MeasurementUnit,
        impedance_ohm: float | None,
        raw_data: str,
    ) -> None:
        user = await self.find_closest_user_to_weight(weight)
        measurement = MeasurementModel(
            measured_at=datetime.now(UTC),
            weight=weight,
            unit=unit,
            impedance_ohm=impedance_ohm,
            raw_data=raw_data,
            user=user,
        )
        self.session.add(measurement)

        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def find_closest_user_to_weight(
        self,
        weight: float,
        threshold_percent: float = DEFAULT_WEIGHT_THRESHOLD_PERCENT,
    ) -> UserModel | None:
        """Find the closest user within the allowed percentage difference in weight."""
        closest_user_id = self._closest_user_id_subquery(weight, threshold_percent)
        return await self.session.scalar(select(UserModel).where(UserModel.id == closest_user_id))

    async def reassign_users_by_weight(
        self,
        threshold_percent: float = DEFAULT_WEIGHT_THRESHOLD_PERCENT,
    ) -> tuple[int, int]:
        """Reassign all measurements and return reference-user and measurement counts."""
        user_count = await self.session.scalar(
            select(func.count(func.distinct(MeasurementModel.user_id))).where(
                MeasurementModel.user_id.is_not(None)
            )
        )
        if not user_count:
            return 0, 0

        measurement_count = (
            await self.session.scalar(select(func.count()).select_from(MeasurementModel)) or 0
        )
        closest_user_id = self._closest_user_id_subquery(
            MeasurementModel.weight,
            threshold_percent,
            MeasurementModel.user_id,
        )
        await self.session.execute(update(MeasurementModel).values(user_id=closest_user_id))
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return user_count, measurement_count

    def _closest_user_id_subquery(
        self,
        weight: ColumnExpressionArgument[float] | float,
        threshold_percent: float,
        current_user_id: ColumnExpressionArgument[int | None] | int | None = None,
    ) -> ScalarSelect[int | None]:
        """Build a scalar query selecting the closest user from latest known weights."""
        if threshold_percent < 0:
            raise ValueError("weight threshold percentage cannot be negative")

        latest_measurements = (
            select(
                MeasurementModel.user_id,
                MeasurementModel.weight,
            )
            .where(MeasurementModel.user_id.is_not(None))
            .distinct(MeasurementModel.user_id)
            .order_by(
                MeasurementModel.user_id,
                MeasurementModel.measured_at.desc(),
                MeasurementModel.id.desc(),
            )
            .subquery()
        )
        distance = func.abs(latest_measurements.c.weight - weight)
        stmt = select(latest_measurements.c.user_id).where(
            distance / latest_measurements.c.weight * 100 <= threshold_percent
        )
        if current_user_id is None:
            stmt = stmt.order_by(distance, latest_measurements.c.user_id)
        else:
            stmt = stmt.order_by(
                distance,
                case((latest_measurements.c.user_id == current_user_id, 0), else_=1),
                latest_measurements.c.user_id,
            )
        return stmt.limit(1).correlate(MeasurementModel).scalar_subquery()

    async def list(
        self,
        limit: int = 50,
    ) -> list[MeasurementModel]:
        stmt = select(MeasurementModel).options(selectinload(MeasurementModel.user))
        stmt = stmt.order_by(
            MeasurementModel.measured_at.desc(),
            MeasurementModel.id.desc(),
        ).limit(limit)
        return list(await self.session.scalars(stmt))

    async def latest(self) -> MeasurementModel | None:
        """Return the latest measurement with its user loaded, if one exists."""
        stmt = select(MeasurementModel).options(selectinload(MeasurementModel.user))
        stmt = stmt.order_by(
            MeasurementModel.measured_at.desc(),
            MeasurementModel.id.desc(),
        ).limit(1)
        return await self.session.scalar(stmt)

    async def update_user(
        self,
        measurement_id: int,
        user_id: int | None,
    ) -> MeasurementModel:
        """Assign a user to a measurement and return it."""
        measurement = await self.session.get(MeasurementModel, measurement_id)
        if measurement is None:
            raise DbEntityNotFoundError(MeasurementModel)

        user = await self.session.get(UserModel, user_id) if user_id is not None else None
        if user_id is not None and user is None:
            raise DbEntityNotFoundError(UserModel)

        measurement.user = user
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return measurement

    async def delete(self, measurement_id: int) -> bool:
        measurement = await self.session.get(MeasurementModel, measurement_id)
        if measurement is None:
            return False

        await self.session.delete(measurement)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return True
