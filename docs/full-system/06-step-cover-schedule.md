# Step Detail - Cover and Schedule

## A) Cover upload flow

### Inputs

- `cover_path` optional

### Pre-validation

1. File must exist.
2. Extension must be in `file_types.supported_image_file_types`.

### Selector keys used

- `cover_edit_button`
- `cover_select_tab`
- `cover_upload_tab`
- `cover_upload_input`
- `cover_upload_confirm`
- `cover_modal_select_tab_name`
- `cover_modal_upload_tab_name`

### Action sequence

1. Click `Edit cover` button.
2. Try optional click for Select tab.
3. Try optional click for Upload tab.
4. Resolve hidden/attached file input with `_find_first_attached`.
5. `set_input_files(cover_path)`.
6. Resolve confirm button by attached state.
7. Try `scroll_into_view_if_needed` + click.
8. If failed, fallback to `click(force=True)`.

### Why this design

- TikTok cover modal changes markup frequently.
- Tabs sometimes renamed or rendered as text nodes.
- Confirm button can be outside viewport.

## B) Schedule flow

### Input

- `schedule` optional UTC datetime

### Normalization rules (before UI actions)

1. If naive datetime, treat as UTC.
2. Convert to UTC timezone.
3. Round minute up to nearest `schedule_minute_multiple` (default 5).
4. Validate range:
- min: now + `schedule_min_minutes` (default 20)
- max: now + `schedule_max_days` (default 10)
5. If out-of-range -> `invalid_schedule`.

### Selector keys used

- `schedule_switch`
- `schedule_date_picker`
- `schedule_calendar`
- `schedule_calendar_month`
- `schedule_calendar_valid_days`
- `schedule_calendar_arrows`
- `schedule_time_picker`
- `schedule_time_picker_container`
- `schedule_timepicker_hours`
- `schedule_timepicker_minutes`

### Date picker logic

1. Enable schedule switch.
2. Open date picker.
3. Parse visible month text.
4. If month mismatch, click prev/next arrow.
5. Iterate valid day nodes and click matching day.
6. If day not found, throw `ui_changed`.

### Time picker logic

1. Open time picker.
2. Wait picker container.
3. Select hour by index `nth(hour)`.
4. Select minute slot by index `nth(minute/5)`.

### Output signals

- Step `set_cover` when cover path provided.
- Step `set_schedule` when schedule provided.
