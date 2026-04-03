# Step Detail - Connect and Navigation

## 1) Connect over CDP

### Code path

- `CDPConnector.connect()` in `infra/cdp.py`

### Action breakdown

1. `sync_playwright().start()`.
2. `chromium.connect_over_cdp(cdp_url)`.
3. Resolve context:
- if no context, throw `no_browser_context`
4. Resolve page:
- first existing page in context, else create one with `context.new_page()`.

### Expected operator setup

- Browser launched with remote-debugging-port exposed.
- Correct profile already logged in TikTok.
- Endpoint reachable from TUC process host.

### Failure contract

- `cdp_connect_failed`:
- `recoverable=true`
- `recommended_action=ensure_debug_port_and_retry`
- `retry_hint=retry_after_environment_fix`

- `no_browser_context`:
- `recoverable=true`
- `recommended_action=open_a_normal_browser_tab_and_retry`

## 2) Navigate to upload URL

### Code path

- `page.goto(req.upload_url, wait_until="domcontentloaded")`

### Default URL

- `https://www.tiktok.com/creator-center/upload?lang=en`

### Notes

- Caller can override with `--upload-url`.
- URL mismatch can lead to selector drift (different product surface).

## 3) Pre-guard checks (first gate)

### Code path

- `_guard_login_and_captcha(page)` in `app/uploader.py`

### Check order

1. `is_login_required(page)`
2. `has_captcha(page)`
3. `has_rate_limit(page)`
4. `has_network_error(page)`

### Why order matters

- Login check first avoids false diagnosis when page is a login wall.
- Captcha/rate/network are terminal for current run and should short-circuit early.

### Output signal

- Success -> step `guard_login_captcha` with `detail=clean`.
- Failure -> `failed` with mapped error code.
