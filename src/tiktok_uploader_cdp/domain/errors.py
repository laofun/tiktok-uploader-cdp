from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ErrorCode(str, Enum):
    CDP_CONNECT_FAILED = "cdp_connect_failed"
    NO_BROWSER_CONTEXT = "no_browser_context"
    NOT_LOGGED_IN = "not_logged_in"
    CAPTCHA_DETECTED = "captcha_detected"
    RATE_LIMITED = "rate_limited"
    CONTENT_REJECTED = "content_rejected"
    NETWORK_ERROR = "network_error"
    UI_CHANGED = "ui_changed"
    FILE_NOT_FOUND = "file_not_found"
    PROCESSING_STUCK = "processing_stuck"
    UPLOAD_TIMEOUT = "upload_timeout"
    POST_FAILED = "post_failed"
    UNKNOWN = "unknown_error"


@dataclass(slots=True)
class UploadError(Exception):
    code: ErrorCode
    message: str
    recoverable: bool
    recommended_action: str

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
