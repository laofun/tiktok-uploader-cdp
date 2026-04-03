from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from tiktok_uploader_cdp.app.uploader import TikTokCDPUploader
from tiktok_uploader_cdp.domain.errors import ErrorCode
from tiktok_uploader_cdp.domain.models import UploadRequest


class DummyLocator:
    def wait_for(self, state: str, timeout: int) -> None:
        return None

    @property
    def first(self):
        return self

    def is_visible(self, timeout: int = 0) -> bool:
        return False

    def set_input_files(self, path: str, timeout: int | None = None) -> None:
        _ = timeout
        return None

    def click(self) -> None:
        return None

    def press(self, key: str) -> None:
        return None

    def fill(self, text: str) -> None:
        return None

    def inner_text(self) -> str:
        return "Your video has been uploaded"

    def get_attribute(self, name: str) -> str:
        _ = name
        return "false"


class DummyPage:
    def __init__(self) -> None:
        self.url = "https://www.tiktok.com/creator-center/upload?lang=en"

    def goto(self, url: str, wait_until: str) -> None:
        self.url = url

    def locator(self, selector: str) -> DummyLocator:
        return DummyLocator()

    def inner_text(self, selector: str) -> str:
        return "normal page"

    def screenshot(self, path: str, full_page: bool) -> None:
        _ = full_page
        with open(path, "wb") as f:
            f.write(b"png")


def test_captcha_detected_returns_structured_error(monkeypatch, tmp_path):
    video = tmp_path / "a.mp4"
    video.write_text("x", encoding="utf-8")

    class DummyConnector:
        def __init__(self, cdp_url: str):
            self.cdp_url = cdp_url

        def connect(self):
            return SimpleNamespace(page=DummyPage())

        def close(self):
            return None

    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.CDPConnector", DummyConnector)
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_captcha", lambda page: True)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.is_login_required", lambda page: False
    )

    result = TikTokCDPUploader().upload(UploadRequest(video_path=str(video)))

    assert result.ok is False
    assert result.error_code == ErrorCode.CAPTCHA_DETECTED
    assert result.recoverable is True
    assert result.recommended_action == "handoff_to_human_solver_and_resume"


def test_ui_changed_returns_stable_error(monkeypatch, tmp_path):
    video = tmp_path / "b.mp4"
    video.write_text("x", encoding="utf-8")

    class DummyConnector:
        def __init__(self, cdp_url: str):
            self.cdp_url = cdp_url

        def connect(self):
            return SimpleNamespace(page=DummyPage())

        def close(self):
            return None

    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.CDPConnector", DummyConnector)
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_captcha", lambda page: False)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.is_login_required", lambda page: False
    )

    def always_fail(*args, **kwargs):
        from tiktok_uploader_cdp.domain.errors import UploadError

        raise UploadError(
            code=ErrorCode.UI_CHANGED,
            message="selectors are outdated",
            recoverable=False,
            recommended_action="update_selectors_then_retry",
        )

    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.find_first_visible", always_fail)

    result = TikTokCDPUploader().upload(UploadRequest(video_path=str(video)))

    assert result.ok is False
    assert result.error_code == ErrorCode.UI_CHANGED
    assert result.recoverable is False
    assert result.recommended_action == "update_selectors_then_retry"


def test_dry_run_stops_before_post(monkeypatch, tmp_path):
    video = tmp_path / "c.mp4"
    video.write_text("x", encoding="utf-8")

    class DummyConnector:
        def __init__(self, cdp_url: str):
            self.cdp_url = cdp_url

        def connect(self):
            return SimpleNamespace(page=DummyPage())

        def close(self):
            return None

    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.CDPConnector", DummyConnector)
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_captcha", lambda page: False)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.is_login_required", lambda page: False
    )

    result = TikTokCDPUploader().upload(
        UploadRequest(video_path=str(video), dry_run=True, request_id="job-xyz")
    )

    assert result.ok is True
    assert result.request_id == "job-xyz"
    assert result.metadata["dry_run"] is True
    assert any(step.name == "dry_run_stop" for step in result.steps)


def test_not_logged_in_error(monkeypatch, tmp_path):
    video = tmp_path / "d.mp4"
    video.write_text("x", encoding="utf-8")

    class DummyConnector:
        def __init__(self, cdp_url: str):
            self.cdp_url = cdp_url

        def connect(self):
            return SimpleNamespace(page=DummyPage())

        def close(self):
            return None

    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.CDPConnector", DummyConnector)
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_captcha", lambda page: False)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.is_login_required", lambda page: True
    )

    result = TikTokCDPUploader().upload(UploadRequest(video_path=str(video)))

    assert result.ok is False
    assert result.error_code == ErrorCode.NOT_LOGGED_IN
    assert result.recommended_action == "user_login_then_retry"
    assert result.retry_hint == "retry_after_environment_fix"


def test_rate_limited_error(monkeypatch, tmp_path):
    video = tmp_path / "e.mp4"
    video.write_text("x", encoding="utf-8")

    class DummyConnector:
        def __init__(self, cdp_url: str):
            self.cdp_url = cdp_url

        def connect(self):
            return SimpleNamespace(page=DummyPage())

        def close(self):
            return None

    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.CDPConnector", DummyConnector)
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_captcha", lambda page: False)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.is_login_required", lambda page: False
    )
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_rate_limit", lambda page: True)

    result = TikTokCDPUploader().upload(UploadRequest(video_path=str(video)))

    assert result.ok is False
    assert result.error_code == ErrorCode.RATE_LIMITED
    assert result.recommended_action == "backoff_and_retry_later"
    assert result.retry_hint == "retry_with_backoff"


def test_post_click_failure_maps_to_post_failed(monkeypatch, tmp_path):
    video = tmp_path / "f.mp4"
    video.write_text("x", encoding="utf-8")

    class ClickFailLocator(DummyLocator):
        def click(self) -> None:
            raise RuntimeError("click blocked")

    class DummyConnector:
        def __init__(self, cdp_url: str):
            self.cdp_url = cdp_url

        def connect(self):
            return SimpleNamespace(page=DummyPage())

        def close(self):
            return None

    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.CDPConnector", DummyConnector)
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_captcha", lambda page: False)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.is_login_required", lambda page: False
    )
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_rate_limit", lambda page: False)

    def stub_find_first_visible(page, selectors, timeout_ms):
        _ = page, timeout_ms
        if selectors == ["xpath=//button[@data-e2e='post_video_button']", "button[data-e2e='post_video_button']"]:
            return ClickFailLocator()
        return DummyLocator()

    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.find_first_visible", stub_find_first_visible
    )

    result = TikTokCDPUploader().upload(UploadRequest(video_path=str(video)))
    assert result.ok is False
    assert result.error_code == ErrorCode.POST_FAILED
    assert result.retry_hint == "retry_once"


def test_error_screenshot_artifact(monkeypatch, tmp_path):
    video = tmp_path / "g.mp4"
    video.write_text("x", encoding="utf-8")
    shot_dir = tmp_path / "shots"

    class DummyConnector:
        def __init__(self, cdp_url: str):
            self.cdp_url = cdp_url

        def connect(self):
            return SimpleNamespace(page=DummyPage())

        def close(self):
            return None

    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.CDPConnector", DummyConnector)
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_captcha", lambda page: True)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.is_login_required", lambda page: False
    )
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_rate_limit", lambda page: False)

    result = TikTokCDPUploader().upload(
        UploadRequest(video_path=str(video), screenshot_dir=str(shot_dir), request_id="job-art")
    )
    assert result.ok is False
    assert result.error_code == ErrorCode.CAPTCHA_DETECTED
    assert "error_screenshot" in result.artifacts


def test_content_rejected_error(monkeypatch, tmp_path):
    video = tmp_path / "h.mp4"
    video.write_text("x", encoding="utf-8")

    class DummyConnector:
        def __init__(self, cdp_url: str):
            self.cdp_url = cdp_url

        def connect(self):
            return SimpleNamespace(page=DummyPage())

        def close(self):
            return None

    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.CDPConnector", DummyConnector)
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_captcha", lambda page: False)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.is_login_required", lambda page: False
    )
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_rate_limit", lambda page: False)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.has_content_rejection", lambda page: True
    )
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_network_error", lambda page: False)

    result = TikTokCDPUploader().upload(UploadRequest(video_path=str(video)))
    assert result.ok is False
    assert result.error_code == ErrorCode.CONTENT_REJECTED
    assert result.recoverable is False
    assert result.recommended_action == "revise_content_then_retry"
    assert result.retry_hint == "do_not_retry_without_content_change"


def test_network_error(monkeypatch, tmp_path):
    video = tmp_path / "i.mp4"
    video.write_text("x", encoding="utf-8")

    class DummyConnector:
        def __init__(self, cdp_url: str):
            self.cdp_url = cdp_url

        def connect(self):
            return SimpleNamespace(page=DummyPage())

        def close(self):
            return None

    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.CDPConnector", DummyConnector)
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_captcha", lambda page: False)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.is_login_required", lambda page: False
    )
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_rate_limit", lambda page: False)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.has_content_rejection", lambda page: False
    )
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_network_error", lambda page: True)

    result = TikTokCDPUploader().upload(UploadRequest(video_path=str(video)))
    assert result.ok is False
    assert result.error_code == ErrorCode.NETWORK_ERROR
    assert result.recoverable is True
    assert result.recommended_action == "check_connectivity_and_retry"
    assert result.retry_hint == "retry_with_backoff"


def test_processing_stuck_error(monkeypatch, tmp_path):
    video = tmp_path / "j.mp4"
    video.write_text("x", encoding="utf-8")

    class DummyConnector:
        def __init__(self, cdp_url: str):
            self.cdp_url = cdp_url

        def connect(self):
            return SimpleNamespace(page=DummyPage())

        def close(self):
            return None

    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.CDPConnector", DummyConnector)
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_captcha", lambda page: False)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.is_login_required", lambda page: False
    )
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_rate_limit", lambda page: False)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.has_content_rejection", lambda page: False
    )
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_network_error", lambda page: False)

    def stuck(*args, **kwargs):
        from tiktok_uploader_cdp.domain.errors import UploadError

        raise UploadError(
            code=ErrorCode.PROCESSING_STUCK,
            message="processing not ready",
            recoverable=True,
            recommended_action="wait_then_retry_once_then_human_review",
        )

    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.TikTokCDPUploader._wait_processing_ready", stuck)

    result = TikTokCDPUploader().upload(UploadRequest(video_path=str(video)))
    assert result.ok is False
    assert result.error_code == ErrorCode.PROCESSING_STUCK
    assert result.retry_hint == "retry_once"


def test_post_now_modal_step(monkeypatch, tmp_path):
    video = tmp_path / "k.mp4"
    video.write_text("x", encoding="utf-8")

    class DummyConnector:
        def __init__(self, cdp_url: str):
            self.cdp_url = cdp_url

        def connect(self):
            return SimpleNamespace(page=DummyPage())

        def close(self):
            return None

    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.CDPConnector", DummyConnector)
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_captcha", lambda page: False)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.is_login_required", lambda page: False
    )
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_rate_limit", lambda page: False)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.has_content_rejection", lambda page: False
    )
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_network_error", lambda page: False)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.TikTokCDPUploader._handle_optional_post_now_modal",
        lambda self, page, cfg: True,
    )

    result = TikTokCDPUploader().upload(UploadRequest(video_path=str(video)))
    assert result.ok is True
    assert any(step.name == "click_post_now_modal" for step in result.steps)


def test_invalid_schedule_rejected(tmp_path):
    video = tmp_path / "l.mp4"
    video.write_text("x", encoding="utf-8")

    bad_schedule = datetime.now(timezone.utc) + timedelta(minutes=5)
    result = TikTokCDPUploader().upload(
        UploadRequest(video_path=str(video), schedule=bad_schedule)
    )
    assert result.ok is False
    assert result.error_code == ErrorCode.INVALID_SCHEDULE


def test_cover_missing_file_returns_file_not_found(tmp_path):
    video = tmp_path / "m.mp4"
    video.write_text("x", encoding="utf-8")

    result = TikTokCDPUploader().upload(
        UploadRequest(video_path=str(video), cover_path=str(tmp_path / "missing.jpg"))
    )
    assert result.ok is False
    assert result.error_code == ErrorCode.FILE_NOT_FOUND


def test_content_modal_flow_adds_expected_steps(monkeypatch, tmp_path):
    video = tmp_path / "n.mp4"
    video.write_text("x", encoding="utf-8")

    class DummyConnector:
        def __init__(self, cdp_url: str):
            self.cdp_url = cdp_url

        def connect(self):
            return SimpleNamespace(page=DummyPage())

        def close(self):
            return None

    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.CDPConnector", DummyConnector)
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_captcha", lambda page: False)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.is_login_required", lambda page: False
    )
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_rate_limit", lambda page: False)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.has_content_rejection", lambda page: False
    )
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_network_error", lambda page: False)
    modal_states = iter([True, False])

    def modal_present(self, page, cfg):
        _ = self, page, cfg
        return next(modal_states, False)

    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.TikTokCDPUploader._is_content_modal_present",
        modal_present,
    )
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.TikTokCDPUploader._click_if_visible",
        lambda self, page, selectors: True,
    )
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.TikTokCDPUploader._set_checkbox_state",
        lambda self, page, selectors, desired: True,
    )

    result = TikTokCDPUploader().upload(
        UploadRequest(
            video_path=str(video),
            content_check_lite=False,
            copyright_check=False,
        )
    )
    assert result.ok is True
    step_names = [s.name for s in result.steps]
    assert "toggle_content_check" in step_names
    assert "continue_content_modal" in step_names
    assert "retry_post_after_content_modal" in step_names


def test_metadata_steps_run_before_wait_processing_ready(monkeypatch, tmp_path):
    video = tmp_path / "o.mp4"
    video.write_text("x", encoding="utf-8")

    class DummyConnector:
        def __init__(self, cdp_url: str):
            self.cdp_url = cdp_url

        def connect(self):
            return SimpleNamespace(page=DummyPage())

        def close(self):
            return None

    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.CDPConnector", DummyConnector)
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_captcha", lambda page: False)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.is_login_required", lambda page: False
    )
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_rate_limit", lambda page: False)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.has_content_rejection", lambda page: False
    )
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_network_error", lambda page: False)

    result = TikTokCDPUploader().upload(UploadRequest(video_path=str(video)))
    assert result.ok is True

    step_names = [s.name for s in result.steps]
    idx = {name: step_names.index(name) for name in step_names}
    assert idx["attach_video"] < idx["set_interactivity"]
    assert idx["set_interactivity"] < idx["set_visibility"]
    assert idx["set_visibility"] < idx["wait_processing_ready"]
    assert idx["wait_processing_ready"] < idx["guard_before_post"]


def test_attach_video_accepts_already_attached_state(monkeypatch, tmp_path):
    video = tmp_path / "p.mp4"
    video.write_text("x", encoding="utf-8")

    class DummyConnector:
        def __init__(self, cdp_url: str):
            self.cdp_url = cdp_url

        def connect(self):
            return SimpleNamespace(page=DummyPage())

        def close(self):
            return None

    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.CDPConnector", DummyConnector)
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_captcha", lambda page: False)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.is_login_required", lambda page: False
    )
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_rate_limit", lambda page: False)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.has_content_rejection", lambda page: False
    )
    monkeypatch.setattr("tiktok_uploader_cdp.app.uploader.has_network_error", lambda page: False)
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.TikTokCDPUploader._try_find_attached_in_page",
        lambda self, page_or_frame, selectors, timeout_ms: None,
    )
    monkeypatch.setattr(
        "tiktok_uploader_cdp.app.uploader.TikTokCDPUploader._is_video_already_attached",
        lambda self, page, video_path, cfg: True,
    )

    result = TikTokCDPUploader().upload(UploadRequest(video_path=str(video)))
    assert result.ok is True
    attach_step = next((s for s in result.steps if s.name == "attach_video"), None)
    assert attach_step is not None
    assert "already_attached" in attach_step.detail
