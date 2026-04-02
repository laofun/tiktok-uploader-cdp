from __future__ import annotations

from playwright.sync_api import Locator, Page

from tiktok_uploader_cdp.domain.errors import ErrorCode, UploadError


def find_first_visible(page: Page, selectors: list[str], timeout_ms: int) -> Locator:
    for selector in selectors:
        try:
            loc = page.locator(selector).first
            loc.wait_for(state="visible", timeout=timeout_ms)
            return loc
        except Exception:
            continue

    raise UploadError(
        code=ErrorCode.UI_CHANGED,
        message=f"No selector matched from candidates: {selectors}",
        recoverable=False,
        recommended_action="update_selectors_then_retry",
    )
