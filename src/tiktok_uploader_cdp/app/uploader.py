from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from os import makedirs
from os.path import exists
from pathlib import Path
from time import sleep

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from tiktok_uploader_cdp.domain.errors import ErrorCode, UploadError
from tiktok_uploader_cdp.domain.models import StepResult, UploadRequest, UploadResult
from tiktok_uploader_cdp.infra.cdp import CDPConnector
from tiktok_uploader_cdp.infra.detectors import (
    has_captcha,
    has_content_rejection,
    has_network_error,
    has_rate_limit,
    is_login_required,
)
from tiktok_uploader_cdp.infra.page_ops import find_first_visible
from tiktok_uploader_cdp.infra.selectors import (
    DESCRIPTION_SELECTORS,
    POST_BUTTON_SELECTORS,
    POST_NOW_MODAL_SELECTORS,
    PUBLISH_CONFIRM_SELECTORS,
    UPLOAD_INPUT_SELECTORS,
)


@dataclass(slots=True)
class TikTokCDPUploader:
    def upload(self, req: UploadRequest) -> UploadResult:
        steps: list[StepResult] = []
        artifacts: dict[str, str] = {}
        if not exists(req.video_path):
            return UploadResult(
                ok=False,
                message=f"Video file not found: {req.video_path}",
                error_code=ErrorCode.FILE_NOT_FOUND,
                recoverable=False,
                recommended_action="fix_input_file_path",
                retry_hint="do_not_retry_without_input_change",
                request_id=req.request_id,
                steps=steps,
                artifacts=artifacts,
            )

        connector = CDPConnector(req.cdp_url)
        try:
            session = connector.connect()
            page = session.page
            steps.append(StepResult("connect_cdp", True, "connected"))

            page.goto(req.upload_url, wait_until="domcontentloaded")
            steps.append(StepResult("goto_upload", True, page.url))

            self._guard_login_and_captcha(page)
            steps.append(StepResult("guard_login_captcha", True, "clean"))

            upload_input = find_first_visible(page, UPLOAD_INPUT_SELECTORS, 10_000)
            upload_input.set_input_files(req.video_path)
            steps.append(StepResult("attach_video", True, req.video_path))
            self._wait_processing_ready(page, 90_000)
            steps.append(StepResult("wait_processing_ready", True, "post_button_enabled"))

            if req.description:
                description_box = find_first_visible(page, DESCRIPTION_SELECTORS, 8_000)
                description_box.click()
                description_box.press("Control+A")
                description_box.press("Backspace")
                description_box.fill(req.description)
                steps.append(
                    StepResult(
                        "set_description",
                        True,
                        f"len={len(req.description)}",
                    )
                )

            self._guard_login_and_captcha(page)
            steps.append(StepResult("guard_before_post", True, "clean"))

            if req.dry_run:
                steps.append(StepResult("dry_run_stop", True, "stopped_before_post"))
                return UploadResult(
                    ok=True,
                    message="Dry run completed (validated flow before posting)",
                    recommended_action="none",
                    retry_hint="none",
                    request_id=req.request_id,
                    steps=steps,
                    artifacts=artifacts,
                    metadata={"final_url": page.url, "dry_run": True},
                )

            post_button = find_first_visible(page, POST_BUTTON_SELECTORS, 10_000)
            try:
                post_button.click()
            except Exception as exc:
                raise UploadError(
                    code=ErrorCode.POST_FAILED,
                    message=f"Unable to click post button: {exc}",
                    recoverable=True,
                    recommended_action="retry_once_then_human_review",
                ) from exc
            steps.append(StepResult("click_post", True, "clicked"))
            if self._handle_optional_post_now_modal(page):
                steps.append(StepResult("click_post_now_modal", True, "clicked"))

            publish_confirmation = find_first_visible(
                page,
                PUBLISH_CONFIRM_SELECTORS,
                req.timeout_seconds * 1000,
            )
            _ = publish_confirmation.inner_text()
            steps.append(StepResult("wait_publish_confirmation", True, "confirmed"))

            return UploadResult(
                ok=True,
                message="Upload completed",
                request_id=req.request_id,
                steps=steps,
                artifacts=artifacts,
                metadata={"final_url": page.url},
            )

        except UploadError as exc:
            screenshot_path = self._capture_error_screenshot(req, page if "page" in locals() else None)
            if screenshot_path:
                artifacts["error_screenshot"] = screenshot_path
            steps.append(
                StepResult(
                    name="failed",
                    ok=False,
                    detail=exc.message,
                    error_code=exc.code,
                )
            )
            return UploadResult(
                ok=False,
                message=exc.message,
                error_code=exc.code,
                recoverable=exc.recoverable,
                recommended_action=exc.recommended_action,
                retry_hint=self._retry_hint(exc.code, exc.recoverable),
                request_id=req.request_id,
                steps=steps,
                artifacts=artifacts,
            )
        except PlaywrightTimeoutError as exc:
            screenshot_path = self._capture_error_screenshot(req, page if "page" in locals() else None)
            if screenshot_path:
                artifacts["error_screenshot"] = screenshot_path
            steps.append(
                StepResult(
                    name="failed",
                    ok=False,
                    detail=str(exc),
                    error_code=ErrorCode.UPLOAD_TIMEOUT,
                )
            )
            return UploadResult(
                ok=False,
                message="Timed out while waiting for upload or publish confirmation",
                error_code=ErrorCode.UPLOAD_TIMEOUT,
                recoverable=True,
                recommended_action="retry_once_then_human_review",
                retry_hint="retry_once",
                request_id=req.request_id,
                steps=steps,
                artifacts=artifacts,
            )
        except Exception as exc:
            screenshot_path = self._capture_error_screenshot(req, page if "page" in locals() else None)
            if screenshot_path:
                artifacts["error_screenshot"] = screenshot_path
            steps.append(
                StepResult(
                    name="failed",
                    ok=False,
                    detail=str(exc),
                    error_code=ErrorCode.UNKNOWN,
                )
            )
            return UploadResult(
                ok=False,
                message=f"Unexpected error: {exc}",
                error_code=ErrorCode.UNKNOWN,
                recoverable=False,
                recommended_action="human_review",
                retry_hint="do_not_retry_without_human_review",
                request_id=req.request_id,
                steps=steps,
                artifacts=artifacts,
            )
        finally:
            connector.close()

    def _guard_login_and_captcha(self, page) -> None:
        if is_login_required(page):
            raise UploadError(
                code=ErrorCode.NOT_LOGGED_IN,
                message="Current browser tab is not authenticated for TikTok",
                recoverable=True,
                recommended_action="user_login_then_retry",
            )

        if has_captcha(page):
            raise UploadError(
                code=ErrorCode.CAPTCHA_DETECTED,
                message="Captcha or anti-bot challenge detected",
                recoverable=True,
                recommended_action="handoff_to_human_solver_and_resume",
            )

        if has_rate_limit(page):
            raise UploadError(
                code=ErrorCode.RATE_LIMITED,
                message="TikTok rate-limited this session",
                recoverable=True,
                recommended_action="backoff_and_retry_later",
            )

        if has_content_rejection(page):
            raise UploadError(
                code=ErrorCode.CONTENT_REJECTED,
                message="TikTok rejected this content under policy/restriction rules",
                recoverable=False,
                recommended_action="revise_content_then_retry",
            )

        if has_network_error(page):
            raise UploadError(
                code=ErrorCode.NETWORK_ERROR,
                message="Network error detected while operating upload flow",
                recoverable=True,
                recommended_action="check_connectivity_and_retry",
            )

    def _retry_hint(self, code: ErrorCode, recoverable: bool) -> str:
        if code == ErrorCode.CAPTCHA_DETECTED:
            return "retry_after_human_step"
        if code == ErrorCode.PROCESSING_STUCK:
            return "retry_once"
        if code == ErrorCode.RATE_LIMITED:
            return "retry_with_backoff"
        if code == ErrorCode.NETWORK_ERROR:
            return "retry_with_backoff"
        if code == ErrorCode.CONTENT_REJECTED:
            return "do_not_retry_without_content_change"
        if code in {ErrorCode.CDP_CONNECT_FAILED, ErrorCode.NOT_LOGGED_IN}:
            return "retry_after_environment_fix"
        if code == ErrorCode.UPLOAD_TIMEOUT and recoverable:
            return "retry_once"
        if code == ErrorCode.UI_CHANGED:
            return "do_not_retry_until_selector_update"
        if recoverable:
            return "retry_once"
        return "do_not_retry_without_human_review"

    def _wait_processing_ready(self, page, timeout_ms: int) -> None:
        post_button = find_first_visible(page, POST_BUTTON_SELECTORS, 10_000)
        deadline = datetime.now(timezone.utc).timestamp() + (timeout_ms / 1000)
        while datetime.now(timezone.utc).timestamp() < deadline:
            state = post_button.get_attribute("data-disabled")
            if state in (None, "false"):
                return
            sleep(0.5)
        raise UploadError(
            code=ErrorCode.PROCESSING_STUCK,
            message="Video processing did not reach ready-to-post state in time",
            recoverable=True,
            recommended_action="wait_then_retry_once_then_human_review",
        )

    def _handle_optional_post_now_modal(self, page) -> bool:
        for selector in POST_NOW_MODAL_SELECTORS:
            try:
                btn = page.locator(selector).first
                if btn.is_visible(timeout=1200):
                    btn.click()
                    return True
            except Exception:
                continue
        return False

    def _capture_error_screenshot(self, req: UploadRequest, page) -> str | None:
        if not req.screenshot_dir or page is None:
            return None
        try:
            makedirs(req.screenshot_dir, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            rid = req.request_id or "no_request_id"
            screenshot_path = str(
                Path(req.screenshot_dir).joinpath(f"error_{rid}_{ts}.png")
            )
            page.screenshot(path=screenshot_path, full_page=True)
            return screenshot_path
        except Exception:
            return None
