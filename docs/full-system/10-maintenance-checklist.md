# Maintenance Checklist

## 1) Before patching

1. Confirm failing phase from `steps[]`.
2. Confirm error bucket from `error_code`.
3. Check whether config-only selector update is sufficient.

## 2) Selector update rules

1. Add, do not replace, existing selectors when possible.
2. Put most specific selector first.
3. Keep generic fallback selectors last.
4. Test with dry-run and one real publish.

## 3) Timeout update rules

1. Increase only the timeout tied to failing step.
2. Avoid global timeout inflation.
3. Record timeout changes in commit description.

## 4) New step / fallback rules

1. Emit explicit `StepResult` names.
2. Keep error code stable unless semantics truly changed.
3. Set `recommended_action` and `retry_hint` coherently.
4. Add tests in `tests/test_uploader_errors.py`.

## 5) OpenClaw compatibility rules

1. Never remove existing `error_code` values without migration.
2. Never change JSON top-level field names.
3. Prefer additive step names over renaming existing steps.
4. Keep failure branch machine-parsable and deterministic.

## 6) Release validation

1. `uv run pytest -q`
2. dry-run on active profile/CDP endpoint
3. one real publish run with screenshot collection
4. verify OpenClaw parser consumes new steps cleanly
