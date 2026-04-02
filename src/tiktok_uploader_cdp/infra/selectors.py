from __future__ import annotations

# Multiple selectors for resilience against TikTok UI changes.
UPLOAD_INPUT_SELECTORS = [
    "input[type='file']",
    "xpath=//input[@type='file']",
]

DESCRIPTION_SELECTORS = [
    "xpath=//div[@contenteditable='true']",
    "div[contenteditable='true']",
]

POST_BUTTON_SELECTORS = [
    "xpath=//button[@data-e2e='post_video_button']",
    "button[data-e2e='post_video_button']",
]

POST_NOW_MODAL_SELECTORS = [
    "xpath=//button[.//div[text()='Post now']]",
    "xpath=//button[contains(., 'Post now')]",
    "button:has-text('Post now')",
]

PUBLISH_CONFIRM_SELECTORS = [
    "xpath=//div[contains(text(), 'Your video has been uploaded') or contains(text(), 'Video published') or contains(text(), '视频已发布')]",
]

LOGIN_BLOCKING_URL_KEYWORDS = ["/login", "/signup"]

CAPTCHA_TEXT_MARKERS = [
    "captcha",
    "verify",
    "drag the puzzle",
    "security check",
    "are you human",
]

CAPTCHA_SELECTORS = [
    "iframe[src*='captcha']",
    "div[class*='captcha']",
    "div[data-e2e*='captcha']",
]
