from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.models.user import User


class AuditService:
    @staticmethod
    def _hash_entry(previous_hash: str | None, payload: dict[str, Any]) -> str:
        canonical = json.dumps(
            {"previous_hash": previous_hash, **payload},
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    async def log_action(
        session: AsyncSession,
        user: User | None,
        action: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        severity: str | None = None,
        tool_called: str | None = None,
        ai_confidence: float | None = None,
        telemetry_data: dict[str, Any] | None = None,
        request_payload: dict[str, Any] | None = None,
        result_payload: dict[str, Any] | None = None,
        ip_address: str | None = None,
        status: str | None = None,
    ) -> AuditLog:
        """
        Creates an immutable audit log entry.
        """
        previous = await session.execute(
            select(AuditLog.entry_hash)
            .where(AuditLog.entry_hash.is_not(None))
            .order_by(AuditLog.timestamp.desc(), AuditLog.id.desc())
            .limit(1)
        )
        previous_hash = previous.scalar_one_or_none()
        payload = {
            "user_id": user.id if user else None,
            "user_role": user.role.value if user else None,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "severity": severity,
            "tool_called": tool_called,
            "ai_confidence": ai_confidence,
            "telemetry_data": telemetry_data,
            "request_payload": request_payload,
            "result_payload": result_payload,
            "ip_address": ip_address,
            "status": status,
        }
        audit_entry = AuditLog(
            user_id=user.id if user else None,
            user_role=user.role.value if user else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            severity=severity,
            tool_called=tool_called,
            ai_confidence=ai_confidence,
            telemetry_data=telemetry_data,
            request_payload=request_payload,
            result_payload=result_payload,
            ip_address=ip_address,
            status=status,
            timestamp=datetime.now(timezone.utc),
            previous_hash=previous_hash,
            entry_hash=AuditService._hash_entry(previous_hash, payload),
        )
        session.add(audit_entry)
        # Flush to get the ID if needed, but not strictly necessary unless we need to return the ID immediately
        # We won't commit here to allow it to be part of the caller's transaction
        await session.flush()
        return audit_entry
