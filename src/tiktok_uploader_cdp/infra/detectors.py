from __future__ import annotations

from playwright.sync_api import Page

from tiktok_uploader_cdp.infra.selectors import (
    CAPTCHA_SELECTORS,
    CAPTCHA_TEXT_MARKERS,
    LOGIN_BLOCKING_URL_KEYWORDS,
)

RATE_LIMIT_TEXT_MARKERS = [
    "too many attempts",
    "try again later",
    "rate limit",
    "temporarily blocked",
]

CONTENT_REJECTED_TEXT_MARKERS = [
    "violates our community guidelines",
    "cannot be posted",
    "content is not eligible",
    "not eligible for recommendation",
    "restricted content",
]

NETWORK_ERROR_TEXT_MARKERS = [
    "network error",
    "you are offline",
    "no internet connection",
    "request failed",
    "failed to fetch",
]


def is_login_required(page: Page) -> bool:
    url = page.url.lower()
    return any(keyword in url for keyword in LOGIN_BLOCKING_URL_KEYWORDS)


def has_captcha(page: Page) -> bool:
    for selector in CAPTCHA_SELECTORS:
        try:
            if page.locator(selector).first.is_visible(timeout=1000):
                return True
        except Exception:
            continue

    try:
        text = page.inner_text("body").lower()
    except Exception:
        return False
    return any(marker in text for marker in CAPTCHA_TEXT_MARKERS)


def has_rate_limit(page: Page) -> bool:
    try:
        text = page.inner_text("body").lower()
    except Exception:
        return False
    return any(marker in text for marker in RATE_LIMIT_TEXT_MARKERS)


def has_content_rejection(page: Page) -> bool:
    try:
        text = page.inner_text("body").lower()
    except Exception:
        return False
    return any(marker in text for marker in CONTENT_REJECTED_TEXT_MARKERS)


def has_network_error(page: Page) -> bool:
    try:
        text = page.inner_text("body").lower()
    except Exception:
        return False
    return any(marker in text for marker in NETWORK_ERROR_TEXT_MARKERS)
