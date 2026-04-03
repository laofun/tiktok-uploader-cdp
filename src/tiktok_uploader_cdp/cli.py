from __future__ import annotations

import argparse
import datetime
import json
import sys
from importlib.metadata import version

from tiktok_uploader_cdp.app.uploader import TikTokCDPUploader
from tiktok_uploader_cdp.domain.models import UploadRequest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Upload TikTok video using existing login over CDP")
    parser.add_argument(
        "--version",
        action="version",
        version=f"tiktok-uploader-cdp {version('tiktok-uploader-cdp')}",
    )
    parser.add_argument("--cdp-url", default="http://127.0.0.1:9222")
    parser.add_argument("--config", default=None)
    parser.add_argument("--video", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument(
        "--schedule",
        default=None,
        help="UTC schedule in format YYYY-MM-DD HH:MM",
    )
    parser.add_argument(
        "--visibility",
        choices=["everyone", "friends", "only_you"],
        default="everyone",
    )
    parser.add_argument("--comment", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--duet", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--stitch", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument(
        "--content-check-lite",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--copyright-check",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--cover", default=None)
    parser.add_argument(
        "--upload-url",
        default="https://www.tiktok.com/creator-center/upload?lang=en",
    )
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--request-id", default=None)
    parser.add_argument("--screenshot-dir", default=None)
    return parser


def parse_schedule(schedule_raw: str | None) -> datetime.datetime | None:
    if not schedule_raw:
        return None
    dt = datetime.datetime.strptime(schedule_raw, "%Y-%m-%d %H:%M")
    return dt.replace(tzinfo=datetime.timezone.utc)


def main() -> None:
    args = build_parser().parse_args()
    request = UploadRequest(
        video_path=args.video,
        description=args.description,
        cdp_url=args.cdp_url,
        config_path=args.config,
        upload_url=args.upload_url,
        timeout_seconds=args.timeout_seconds,
        schedule=parse_schedule(args.schedule),
        visibility=args.visibility,
        comment=args.comment,
        duet=args.duet,
        stitch=args.stitch,
        cover_path=args.cover,
        content_check_lite=args.content_check_lite,
        copyright_check=args.copyright_check,
        dry_run=args.dry_run,
        request_id=args.request_id,
        screenshot_dir=args.screenshot_dir,
    )

    result = TikTokCDPUploader().upload(request)
    print(json.dumps(result.to_dict(), ensure_ascii=True))
    sys.exit(0 if result.ok else 1)


if __name__ == "__main__":
    main()
