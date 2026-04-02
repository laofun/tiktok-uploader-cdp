from __future__ import annotations

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from tiktok_uploader_cdp.domain.errors import ErrorCode, UploadError


class CDPSession:
    def __init__(self, browser: Browser, context: BrowserContext, page: Page):
        self.browser = browser
        self.context = context
        self.page = page


class CDPConnector:
    def __init__(self, cdp_url: str):
        self.cdp_url = cdp_url
        self._playwright = None

    def connect(self) -> CDPSession:
        try:
            self._playwright = sync_playwright().start()
            browser = self._playwright.chromium.connect_over_cdp(self.cdp_url)
        except Exception as exc:
            raise UploadError(
                code=ErrorCode.CDP_CONNECT_FAILED,
                message=f"Cannot connect over CDP: {exc}",
                recoverable=True,
                recommended_action="ensure_debug_port_and_retry",
            ) from exc

        if not browser.contexts:
            browser.close()
            raise UploadError(
                code=ErrorCode.NO_BROWSER_CONTEXT,
                message="Connected to browser but no contexts are available",
                recoverable=True,
                recommended_action="open_a_normal_browser_tab_and_retry",
            )

        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        return CDPSession(browser=browser, context=context, page=page)

    def close(self) -> None:
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None
