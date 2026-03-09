from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Link(Base):
    __tablename__ = 'links'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    short_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    original_url: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    click_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'), nullable=True)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey('projects.id'), nullable=True)

    owner = relationship('User', back_populates='links')
    project = relationship('Project', back_populates='links')
