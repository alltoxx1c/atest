"""ORM-модели SQLAlchemy."""

from datetime import datetime, timezone

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Round(Base):
    """Один сыгранный раунд."""

    __tablename__ = "rounds"

    id: Mapped[int] = mapped_column(primary_key=True)
    player: Mapped[str] = mapped_column(String(16))
    computer: Mapped[str] = mapped_column(String(16))
    result: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
