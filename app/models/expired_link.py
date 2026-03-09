from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ExpiredLink(Base):
    __tablename__ = 'expired_links'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    short_code: Mapped[str] = mapped_column(String(50), nullable=False)
    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expired_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    click_count: Mapped[int] = mapped_column(Integer, nullable=False)
