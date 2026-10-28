from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.services.audit_service import AuditService


async def verify_audit_chain(session: AsyncSession) -> dict[str, Any]:
    result = await session.execute(select(AuditLog).order_by(AuditLog.timestamp.asc(), AuditLog.id.asc()))
    entries = list(result.scalars().all())
    previous_hash = None
    for index, entry in enumerate(entries):
        payload = {
            "user_id": entry.user_id,
            "user_role": entry.user_role,
            "action": entry.action,
            "resource_type": entry.resource_type,
            "resource_id": entry.resource_id,
            "severity": entry.severity,
            "tool_called": entry.tool_called,
            "ai_confidence": entry.ai_confidence,
            "telemetry_data": entry.telemetry_data,
            "request_payload": entry.request_payload,
            "result_payload": entry.result_payload,
            "ip_address": entry.ip_address,
            "status": entry.status,
        }
        expected = AuditService._hash_entry(previous_hash, payload)
        if entry.previous_hash != previous_hash or entry.entry_hash != expected:
            return {"valid": False, "checked": index + 1, "failed_entry_id": entry.id}
        previous_hash = entry.entry_hash
    return {"valid": True, "checked": len(entries), "head": previous_hash}
