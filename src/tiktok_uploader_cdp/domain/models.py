from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from tiktok_uploader_cdp.domain.errors import ErrorCode


@dataclass(slots=True)
class UploadRequest:
    video_path: str
    description: str = ""
    cdp_url: str = "http://127.0.0.1:9222"
    upload_url: str = "https://www.tiktok.com/creator-center/upload?lang=en"
    timeout_seconds: int = 120
    dry_run: bool = False
    request_id: str | None = None
    screenshot_dir: str | None = None


@dataclass(slots=True)
class StepResult:
    name: str
    ok: bool
    detail: str
    error_code: ErrorCode | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["error_code"] = self.error_code.value if self.error_code else None
        return payload


@dataclass(slots=True)
class UploadResult:
    ok: bool
    message: str
    error_code: ErrorCode | None = None
    recoverable: bool = False
    recommended_action: str = "none"
    retry_hint: str = "none"
    schema_version: str = "1.1.0"
    request_id: str | None = None
    created_at_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    steps: list[StepResult] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "message": self.message,
            "error_code": self.error_code.value if self.error_code else None,
            "recoverable": self.recoverable,
            "recommended_action": self.recommended_action,
            "retry_hint": self.retry_hint,
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "created_at_utc": self.created_at_utc,
            "steps": [step.to_dict() for step in self.steps],
            "artifacts": self.artifacts,
            "metadata": self.metadata,
        }
