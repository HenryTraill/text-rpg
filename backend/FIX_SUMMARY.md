# Fix for GitHub Issue #40: Tests Being Skipped in GitHub Actions

## Problem
- 55 tests were being skipped in GitHub Actions
- Error message: `PytestUnhandledCoroutineWarning: async def functions are not natively supported and have been skipped`
- pytest-asyncio was installed but not being recognized

## Root Cause
The `pytest.ini` file was using `[tool:pytest]` as the section header, which is incorrect:
- `[tool:pytest]` is for `setup.cfg` files
- `pytest.ini` files should use `[pytest]` as the section header

This caused pytest to ignore the configuration, including the crucial `asyncio_mode = auto` setting.

## Solution
Changed the section header in `backend/pytest.ini` from `[tool:pytest]` to `[pytest]`

## Result
- pytest will now properly read the configuration
- `asyncio_mode = auto` will be recognized
- pytest-asyncio will handle async tests correctly
- All 55 previously skipped tests should now run

## Verification
After this fix is merged, the GitHub Actions workflow should show:
- No more `PytestUnhandledCoroutineWarning` messages
- All async tests running (not skipped)
- Improved test coverage as all tests are executed