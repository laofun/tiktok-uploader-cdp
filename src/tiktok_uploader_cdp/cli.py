from __future__ import annotations

import argparse
import json
import sys

from tiktok_uploader_cdp.app.uploader import TikTokCDPUploader
from tiktok_uploader_cdp.domain.models import UploadRequest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Upload TikTok video using existing login over CDP")
    parser.add_argument("--cdp-url", default="http://127.0.0.1:9222")
    parser.add_argument("--video", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument(
        "--upload-url",
        default="https://www.tiktok.com/creator-center/upload?lang=en",
    )
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--request-id", default=None)
    parser.add_argument("--screenshot-dir", default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    request = UploadRequest(
        video_path=args.video,
        description=args.description,
        cdp_url=args.cdp_url,
        upload_url=args.upload_url,
        timeout_seconds=args.timeout_seconds,
        dry_run=args.dry_run,
        request_id=args.request_id,
        screenshot_dir=args.screenshot_dir,
    )

    result = TikTokCDPUploader().upload(request)
    print(json.dumps(result.to_dict(), ensure_ascii=True))
    sys.exit(0 if result.ok else 1)


if __name__ == "__main__":
    main()
