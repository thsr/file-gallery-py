**[2026-06-18] HTML template tweaks**

**[2026-06-16] Added `.gardenkeep` skip support**

* Folders containing a `.gardenkeep` file are listed in the parent gallery but not traversed — no `index.html` is generated for them or their descendants.

**[2026-06-16] Added section comments in `cultivate.py`**

**[2026-05-17] Added verbose debugging mode**

* Introduced a new `-v` or `--verbose` command line argument to toggle debug outputs

**[2026-05-17 updates] .DS_Store Parsing Fixes & Finder Sync Enhancement**

*   **Fixed `.DS_Store` Import Error**: Corrected module import to `from ds_store import DSStore`.
*   **Added `force_ds_store_update` Feature**: Added a pre-run AppleScript hook to force macOS Finder to flush its memory cache and save icon positions to `.DS_Store` immediately.

**[2026-05-17 initial Python rewrite] Ported from JavaScript (inchkev/file-gallery)**

*   **Complete Rewrite**: Ported the core static site generator from JavaScript/Node.js to Python.
*   **Templating Engine**: Migrated HTML generation to `Jinja2`.
*   **Dependency Replacements**: Replaced JavaScript dependencies with Python equivalents (PIL, pathspec, markdown, ds-store).
*   **Concurrency**: Added `ThreadPoolExecutor` for asynchronous, parallel file parsing.
*   **Type Hinting & Dataclasses**: Refactored core logic to use Python `dataclasses` and strong typing.
