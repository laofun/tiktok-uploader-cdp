from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
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
from tiktok_uploader_cdp.infra.runtime_config import RuntimeConfig, load_runtime_config


@dataclass(slots=True)
class TikTokCDPUploader:
    def upload(self, req: UploadRequest) -> UploadResult:
        steps: list[StepResult] = []
        artifacts: dict[str, str] = {}

        cfg = load_runtime_config(req.config_path)

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

        if req.cover_path and not exists(req.cover_path):
            return UploadResult(
                ok=False,
                message=f"Cover file not found: {req.cover_path}",
                error_code=ErrorCode.FILE_NOT_FOUND,
                recoverable=False,
                recommended_action="fix_cover_file_path",
                retry_hint="do_not_retry_without_input_change",
                request_id=req.request_id,
                steps=steps,
                artifacts=artifacts,
            )

        try:
            normalized_schedule = self._normalize_schedule(req.schedule, cfg)
        except UploadError as exc:
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

        connector = CDPConnector(req.cdp_url)
        try:
            session = connector.connect()
            page = session.page
            steps.append(StepResult("connect_cdp", True, "connected"))

            page.goto(req.upload_url, wait_until="domcontentloaded")
            steps.append(StepResult("goto_upload", True, page.url))

            self._guard_login_and_captcha(page)
            steps.append(StepResult("guard_login_captcha", True, "clean"))

            upload_input = find_first_visible(
                page,
                cfg.selectors_list("upload_input"),
                self._ms(cfg, "implicit_wait_seconds", 30),
            )
            upload_input.set_input_files(req.video_path)
            steps.append(StepResult("attach_video", True, req.video_path))

            self._wait_processing_ready(
                page,
                self._ms(cfg, "processing_ready_timeout_seconds", 90),
                cfg,
            )
            steps.append(StepResult("wait_processing_ready", True, "post_button_enabled"))

            self._set_interactivity(page, req.comment, req.duet, req.stitch, cfg)
            steps.append(
                StepResult(
                    "set_interactivity",
                    True,
                    f"comment={req.comment},duet={req.duet},stitch={req.stitch}",
                )
            )

            self._set_visibility(page, req.visibility, cfg)
            steps.append(StepResult("set_visibility", True, req.visibility))

            if req.description:
                self._set_description(page, req.description, cfg)
                steps.append(StepResult("set_description", True, f"len={len(req.description)}"))

            if req.cover_path:
                self._set_cover(page, req.cover_path, cfg)
                steps.append(StepResult("set_cover", True, req.cover_path))

            if normalized_schedule is not None:
                self._set_schedule(page, normalized_schedule, cfg)
                steps.append(
                    StepResult(
                        "set_schedule",
                        True,
                        normalized_schedule.isoformat(),
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

            post_button = find_first_visible(
                page,
                cfg.selectors_list("post_button"),
                self._ms(cfg, "implicit_wait_seconds", 30),
            )
            self._click_post_button(post_button)
            steps.append(StepResult("click_post", True, "clicked"))

            if self._handle_optional_post_now_modal(page, cfg):
                steps.append(StepResult("click_post_now_modal", True, "clicked"))

            content_steps, should_retry_post = self._handle_content_restriction_modal(
                page,
                req,
                cfg,
            )
            steps.extend(content_steps)

            if should_retry_post:
                post_button = find_first_visible(
                    page,
                    cfg.selectors_list("post_button"),
                    self._ms(cfg, "implicit_wait_seconds", 30),
                )
                self._click_post_button(post_button)
                steps.append(StepResult("retry_post_after_content_modal", True, "clicked"))

            publish_confirmation = find_first_visible(
                page,
                cfg.selectors_list("publish_confirm"),
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

    def _ms(self, cfg: RuntimeConfig, key: str, default_seconds: int) -> int:
        return int(cfg.timeouts.get(key, default_seconds)) * 1000

    def _normalize_schedule(
        self,
        schedule: datetime | None,
        cfg: RuntimeConfig,
    ) -> datetime | None:
        if schedule is None:
            return None

        if schedule.tzinfo is None:
            schedule = schedule.replace(tzinfo=timezone.utc)

        schedule = schedule.astimezone(timezone.utc)

        minute_multiple = int(cfg.limits.get("schedule_minute_multiple", 5))
        if schedule.minute % minute_multiple != 0:
            schedule += timedelta(minutes=(minute_multiple - (schedule.minute % minute_multiple)))
            schedule = schedule.replace(second=0, microsecond=0)

        now = datetime.now(timezone.utc)
        min_dt = now + timedelta(minutes=int(cfg.limits.get("schedule_min_minutes", 20)))
        max_dt = now + timedelta(days=int(cfg.limits.get("schedule_max_days", 10)))

        if schedule < min_dt or schedule > max_dt:
            raise UploadError(
                code=ErrorCode.INVALID_SCHEDULE,
                message="Schedule must be 20 minutes to 10 days in the future (UTC)",
                recoverable=False,
                recommended_action="fix_schedule_and_retry",
            )
        return schedule

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

        if has_network_error(page):
            raise UploadError(
                code=ErrorCode.NETWORK_ERROR,
                message="Network error detected while operating upload flow",
                recoverable=True,
                recommended_action="check_connectivity_and_retry",
            )

    def _set_interactivity(
        self,
        page,
        comment: bool,
        duet: bool,
        stitch: bool,
        cfg: RuntimeConfig,
    ) -> None:
        self._set_toggle(page, cfg.selectors_list("comment_toggle"), comment)
        self._set_toggle(page, cfg.selectors_list("duet_toggle"), duet)
        self._set_toggle(page, cfg.selectors_list("stitch_toggle"), stitch)

    def _set_toggle(self, page, selectors: list[str], desired: bool) -> None:
        if not selectors:
            return
        try:
            toggle = find_first_visible(page, selectors, 5000)
            current = True
            try:
                current = bool(toggle.is_checked())
            except Exception:
                pass
            if current ^ desired:
                toggle.click()
        except Exception:
            return

    def _set_visibility(self, page, visibility: str, cfg: RuntimeConfig) -> None:
        if visibility == "everyone":
            return

        text_map = {
            "everyone": "Everyone",
            "friends": "Friends",
            "only_you": "Only you",
        }

        dropdown = find_first_visible(
            page,
            cfg.selectors_list("visibility_dropdown"),
            8000,
        )
        dropdown.click()
        sleep(1)

        option_xpath_template = cfg.selector_string(
            "visibility_option_xpath_template",
            "//div[@role='option' and contains(., '{text}')]",
        )
        option_xpath = option_xpath_template.format(text=text_map.get(visibility, "Everyone"))
        option = page.locator(f"xpath={option_xpath}").first
        option.scroll_into_view_if_needed()
        option.click()

    def _set_description(self, page, description: str, cfg: RuntimeConfig) -> None:
        desc = find_first_visible(page, cfg.selectors_list("description"), 8000)
        desc.click()
        desc.press("Control+A")
        desc.press("Backspace")

        words = description.split(" ")
        for word in words:
            if not word:
                continue

            if word.startswith("#"):
                self._type_word(desc, word)
                sleep(0.3)
                try:
                    mention_box = find_first_visible(
                        page,
                        cfg.selectors_list("mention_box"),
                        self._ms(cfg, "add_hashtag_wait_seconds", 5),
                    )
                    if mention_box.is_visible():
                        desc.press("Enter")
                except Exception:
                    pass
                desc.press_sequentially(" ")
                continue

            if word.startswith("@"):
                self._type_word(desc, word)
                sleep(0.5)
                try:
                    users = page.locator(cfg.selectors_list("mention_user_id")[0]).all()
                    target = word[1:].lower()
                    chosen = False
                    for i, user in enumerate(users):
                        if user.is_visible():
                            text = user.inner_text().split(" ")[0].lower()
                            if text == target:
                                for _ in range(i):
                                    desc.press("ArrowDown")
                                desc.press("Enter")
                                chosen = True
                                break
                    if not chosen:
                        desc.press_sequentially(" ")
                except Exception:
                    desc.press_sequentially(" ")
                continue

            self._type_word(desc, word + " ")

    def _type_word(self, locator, value: str) -> None:
        try:
            locator.press_sequentially(value, delay=50)
        except Exception:
            locator.type(value)

    def _set_cover(self, page, cover_path: str, cfg: RuntimeConfig) -> None:
        allowed = set(cfg.file_types.get("supported_image_file_types", ["png", "jpg", "jpeg"]))
        ext = cover_path.split(".")[-1].lower()
        if ext not in allowed:
            raise UploadError(
                code=ErrorCode.UNKNOWN,
                message=f"Unsupported cover extension: {ext}",
                recoverable=False,
                recommended_action="use_supported_cover_extension",
            )

        edit_btn = find_first_visible(page, cfg.selectors_list("cover_edit_button"), 8000)
        edit_btn.click()

        # Cover modal often changes markup; try select tab then upload tab.
        self._click_optional_tab(
            page,
            cfg.selectors_list("cover_select_tab"),
            cfg.selector_string("cover_modal_select_tab_name", "Select cover"),
        )
        self._click_optional_tab(
            page,
            cfg.selectors_list("cover_upload_tab"),
            cfg.selector_string("cover_modal_upload_tab_name", "Upload cover"),
        )

        upload_input = self._find_first_attached(page, cfg.selectors_list("cover_upload_input"), 6000)
        upload_input.set_input_files(cover_path)
        confirm = self._find_first_attached(page, cfg.selectors_list("cover_upload_confirm"), 6000)
        try:
            confirm.scroll_into_view_if_needed()
            confirm.click()
        except Exception:
            confirm.click(force=True)

    def _set_schedule(self, page, schedule: datetime, cfg: RuntimeConfig) -> None:
        switch = find_first_visible(page, cfg.selectors_list("schedule_switch"), 8000)
        switch.click()

        self._pick_schedule_date(page, schedule.month, schedule.day, cfg)
        self._pick_schedule_time(page, schedule.hour, schedule.minute, cfg)

    def _pick_schedule_date(self, page, month: int, day: int, cfg: RuntimeConfig) -> None:
        date_picker = find_first_visible(page, cfg.selectors_list("schedule_date_picker"), 8000)
        date_picker.click()

        _ = find_first_visible(page, cfg.selectors_list("schedule_calendar"), 5000)
        month_locator = find_first_visible(page, cfg.selectors_list("schedule_calendar_month"), 5000)
        month_text = month_locator.inner_text().strip()
        try:
            visible_month = datetime.strptime(month_text, "%B").month
        except Exception:
            visible_month = month

        if visible_month != month:
            arrows = page.locator(cfg.selectors_list("schedule_calendar_arrows")[0])
            if visible_month < month:
                arrows.last.click()
            else:
                arrows.first.click()

        days = page.locator(cfg.selectors_list("schedule_calendar_valid_days")[0]).all()
        for d in days:
            try:
                if int(d.inner_text().strip()) == day:
                    d.click()
                    return
            except Exception:
                continue

        raise UploadError(
            code=ErrorCode.UI_CHANGED,
            message="Schedule day selector not found",
            recoverable=False,
            recommended_action="update_selectors_then_retry",
        )

    def _pick_schedule_time(self, page, hour: int, minute: int, cfg: RuntimeConfig) -> None:
        time_picker = find_first_visible(page, cfg.selectors_list("schedule_time_picker"), 8000)
        time_picker.click()

        _ = find_first_visible(page, cfg.selectors_list("schedule_time_picker_container"), 5000)

        hour_options = page.locator(cfg.selectors_list("schedule_timepicker_hours")[0])
        minute_options = page.locator(cfg.selectors_list("schedule_timepicker_minutes")[0])

        hour_el = hour_options.nth(hour)
        minute_el = minute_options.nth(int(minute / 5))

        hour_el.scroll_into_view_if_needed()
        hour_el.click()
        minute_el.scroll_into_view_if_needed()
        minute_el.click()

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
        if code == ErrorCode.INVALID_SCHEDULE:
            return "do_not_retry_without_input_change"
        if code in {ErrorCode.CDP_CONNECT_FAILED, ErrorCode.NOT_LOGGED_IN}:
            return "retry_after_environment_fix"
        if code == ErrorCode.UPLOAD_TIMEOUT and recoverable:
            return "retry_once"
        if code == ErrorCode.UI_CHANGED:
            return "do_not_retry_until_selector_update"
        if recoverable:
            return "retry_once"
        return "do_not_retry_without_human_review"

    def _wait_processing_ready(self, page, timeout_ms: int, cfg: RuntimeConfig) -> None:
        post_button = find_first_visible(page, cfg.selectors_list("post_button"), 10_000)
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

    def _handle_optional_post_now_modal(self, page, cfg: RuntimeConfig) -> bool:
        for selector in cfg.selectors_list("post_now_modal"):
            try:
                btn = page.locator(selector).first
                if btn.is_visible(timeout=1200):
                    btn.click()
                    return True
            except Exception:
                continue
        return False

    def _click_post_button(self, post_button) -> None:
        try:
            post_button.scroll_into_view_if_needed()
        except Exception:
            pass
        try:
            post_button.click()
        except Exception:
            try:
                post_button.click(force=True)
            except Exception as exc:
                raise UploadError(
                    code=ErrorCode.POST_FAILED,
                    message=f"Unable to click post button: {exc}",
                    recoverable=True,
                    recommended_action="retry_once_then_human_review",
                ) from exc

    def _click_optional_tab(self, page, selectors: list[str], tab_name: str) -> bool:
        for selector in selectors:
            try:
                tab = page.locator(selector).first
                if tab.is_visible(timeout=1200):
                    tab.click()
                    return True
            except Exception:
                continue
        try:
            tab = page.get_by_text(tab_name).first
            if tab.is_visible(timeout=1200):
                tab.click()
                return True
        except Exception:
            pass
        return False

    def _find_first_attached(self, page, selectors: list[str], timeout_ms: int):
        for selector in selectors:
            try:
                loc = page.locator(selector).first
                loc.wait_for(state="attached", timeout=timeout_ms)
                return loc
            except Exception:
                continue
        raise UploadError(
            code=ErrorCode.UI_CHANGED,
            message=f"No attached selector matched from candidates: {selectors}",
            recoverable=False,
            recommended_action="update_selectors_then_retry",
        )

    def _handle_content_restriction_modal(
        self,
        page,
        req: UploadRequest,
        cfg: RuntimeConfig,
    ) -> tuple[list[StepResult], bool]:
        steps: list[StepResult] = []
        modal_present = self._is_content_modal_present(page, cfg) or has_content_rejection(page)
        if not modal_present:
            return steps, False

        self._click_if_visible(page, cfg.selectors_list("content_modal_view_details"))

        toggle_actions: list[str] = []
        if not req.content_check_lite:
            if self._set_checkbox_state(page, cfg.selectors_list("content_check_lite_toggle"), False):
                toggle_actions.append("content_check_lite=off")
        if not req.copyright_check:
            if self._set_checkbox_state(page, cfg.selectors_list("copyright_check_toggle"), False):
                toggle_actions.append("copyright_check=off")
        steps.append(
            StepResult(
                "toggle_content_check",
                True,
                ",".join(toggle_actions) if toggle_actions else "no_toggle_change",
            )
        )

        continued = self._click_if_visible(page, cfg.selectors_list("content_modal_continue"))
        if not continued:
            self._click_if_visible(page, cfg.selectors_list("content_modal_close"))
        steps.append(
            StepResult(
                "continue_content_modal",
                True,
                "continue_clicked" if continued else "modal_closed",
            )
        )

        sleep(1)
        if self._is_content_modal_present(page, cfg) or has_content_rejection(page):
            raise UploadError(
                code=ErrorCode.CONTENT_REJECTED,
                message="TikTok flagged the video as content-restricted after posting",
                recoverable=False,
                recommended_action="revise_content_then_retry",
            )
        return steps, True

    def _is_content_modal_present(self, page, cfg: RuntimeConfig) -> bool:
        for selector in cfg.selectors_list("content_modal"):
            try:
                if page.locator(selector).first.is_visible(timeout=1000):
                    return True
            except Exception:
                continue
        return False

    def _click_if_visible(self, page, selectors: list[str]) -> bool:
        for selector in selectors:
            try:
                el = page.locator(selector).first
                if el.is_visible(timeout=1200):
                    try:
                        el.scroll_into_view_if_needed()
                    except Exception:
                        pass
                    try:
                        el.click()
                    except Exception:
                        el.click(force=True)
                    return True
            except Exception:
                continue
        return False

    def _set_checkbox_state(self, page, selectors: list[str], desired: bool) -> bool:
        for selector in selectors:
            try:
                cb = page.locator(selector).first
                cb.wait_for(state="attached", timeout=1500)
                try:
                    current = bool(cb.is_checked())
                except Exception:
                    current = desired
                if current != desired:
                    try:
                        cb.click()
                    except Exception:
                        cb.click(force=True)
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
