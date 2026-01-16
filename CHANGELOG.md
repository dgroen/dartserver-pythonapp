## 2026-01-12
 - **Bugfix (dartboard config)**: Fixed `TypeError` in dartboard type registration and mapping import:
   - Removed unsupported `master_pins`/`slave_pins` keyword arguments from `DartboardService.register_dartboard_type()` call.
   - Decoupled pin validation into a separate `update_dartboard_pins()` step when pins are provided.
   - Added guard to reject invalid boardType `'__new__'` in mapping import endpoint with a clear error message.
   - Corrected indentation in `app_services.py` bulk import response.
## 2025-11-21
 - deploy test
