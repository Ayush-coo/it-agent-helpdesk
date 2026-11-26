from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    timestamp = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_id = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_role = mapped_column(String(20), nullable=True)
    action = mapped_column(String(100), nullable=False)
    resource_type = mapped_column(String(50), nullable=True)
    resource_id = mapped_column(String(36), nullable=True, index=True)
    severity = mapped_column(String(4), nullable=True)
    tool_called = mapped_column(String(100), nullable=True)
    ai_confidence = mapped_column(Float, nullable=True)
    telemetry_data = mapped_column(JSON, nullable=True)
    request_payload = mapped_column(JSON, nullable=True)
    result_payload = mapped_column(JSON, nullable=True)
    ip_address = mapped_column(String(45), nullable=True)
    status = mapped_column(String(20), nullable=True)
    previous_hash = mapped_column(String(64), nullable=True)
    entry_hash = mapped_column(String(64), nullable=True, index=True)
