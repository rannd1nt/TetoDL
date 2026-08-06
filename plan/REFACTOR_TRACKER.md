# REFACTOR TRACKER — 3-Layer Architecture Migration

> **Branch:** `refactor/restructure`
> **Base:** `main` (73a5095)
> **Goal:** Transform `tetodl/` into 3 clean layers (`ui/`, `core/`, `utils/`).

---

## 1. Import Change Tracker

Every file that moves must have its import paths updated. This table tracks every file with its old path, new path, and all imports that need rewrites.

### 1a. `core/domain/` — Phase 0

| File | Old imports | New imports | Status |
|---|---|---|---|
| `core/domain/models.py` | (moved from `core/models.py`) | `tetodl.core.models` → `tetodl.core.domain.models` | PENDING |
| `core/domain/config.py` | (moved from `core/config.py`) | `tetodl.core.config` → `tetodl.core.domain.config` | PENDING |
| `core/domain/cache.py` | (moved from `core/cache.py`) | `tetodl.core.cache` → `tetodl.core.domain.cache` | PENDING |
| `core/domain/history.py` | (moved from `core/history.py`) | `tetodl.core.history` → `tetodl.core.domain.history` | PENDING |
| `core/domain/tagger.py` | (moved from `core/tagger.py`) | `tetodl.core.tagger` → `tetodl.core.domain.tagger` | PENDING |
| `core/domain/registry.py` | (moved from `core/registry.py`) | `tetodl.core.registry` → `tetodl.core.domain.registry` | PENDING |
| `core/domain/step.py` | (moved from `core/step.py`) | `tetodl.core.step` → `tetodl.core.domain.step` | PENDING |
| `core/domain/env.py` | (moved from `core/env.py`) | `tetodl.core.env` → `tetodl.core.domain.env` | PENDING |
| `core/domain/exceptions.py` | (new file) | — | PENDING |

### 1b. `core/services/cover/` → `core/cover/` — Phase 1

| File | Old path | New path | Import changes | Status |
|---|---|---|---|---|
| `core/cover/__init__.py` | `services/cover/__init__.py` | `core/cover/__init__.py` | `tetodl.services.cover` → `tetodl.core.cover` | PENDING |
| `core/cover/image.py` | `services/cover/image.py` | `core/cover/image.py` | Same | PENDING |
| `core/cover/models.py` | `services/cover/models.py` | `core/cover/models.py` | Same | PENDING |
| `core/cover/processor.py` | `services/cover/processor.py` | `core/cover/processor.py` | Same | PENDING |
| `core/cover/providers/base.py` | `services/cover/providers/base.py` | `core/cover/providers/base.py` | Same | PENDING |
| `core/cover/providers/deezer.py` | `services/cover/providers/deezer.py` | `core/cover/providers/deezer.py` | Same | PENDING |
| `core/cover/providers/genius.py` | `services/cover/providers/genius.py` | `core/cover/providers/genius.py` | Same | PENDING |
| `core/cover/providers/itunes.py` | `services/cover/providers/itunes.py` | `core/cover/providers/itunes.py` | Same | PENDING |

**Files importing from old path:**
```bash
grep -r "tetodl.services.cover" tetodl/
# → pipeline/steps/cover.py, pipeline/steps/lyrics.py, etc.
```

### 1c. `pipeline/` → `core/pipeline/` — Phase 2

| File | Old path | New path | Import changes | Status |
|---|---|---|---|---|
| `core/pipeline/__init__.py` | `pipeline/__init__.py` | `core/pipeline/__init__.py` | `tetodl.pipeline` → `tetodl.core.pipeline` | DONE |
| `core/pipeline/runner.py` | `pipeline/pipeline.py` | `core/pipeline/runner.py` | Same + rename | DONE |
| `core/pipeline/handlers.py` | `pipeline/handlers.py` | `core/pipeline/handlers.py` | Same + fix constants/env + fix UIProvider import | DONE |
| `core/pipeline/stages/classify.py` | `pipeline/steps/classify.py` | `core/pipeline/stages/classify.py` | Same + rename | DONE |
| `core/pipeline/stages/cover.py` | `pipeline/steps/cover.py` | `core/pipeline/stages/cover.py` | Same + rename; old `tetodl.lyrics.cleaner` → `tetodl.core.pipeline.cleaners.title`; `tetodl.services.cover` → `tetodl.core.cover` | DONE |
| `core/pipeline/stages/download.py` | `pipeline/steps/download.py` | `core/pipeline/stages/download.py` | Same + rename; `constants.FFMPEG_CMD`/`YTDLP_CACHE_DIR` → `env.get(...)` | DONE |
| `core/pipeline/stages/extract.py` | `pipeline/steps/extract.py` | `core/pipeline/stages/extract.py` | Same + rename; remove `import tetodl.extractors` (auto-register no longer needed) | DONE |
| `core/pipeline/stages/finalize.py` | `pipeline/steps/finalize.py` | `core/pipeline/stages/finalize.py` | Same + rename; old `core.cache`/`core.history` → `core.domain.cache`/`core.domain.history` | DONE |
| `core/pipeline/stages/lyrics.py` | `pipeline/steps/lyrics.py` | `core/pipeline/stages/lyrics.py` | Same + rename; old `tetodl.lyrics` → `tetodl.core.lyrics`/`core.pipeline.cleaners.title` | DONE |
| `core/pipeline/context.py` | *(new)* | `core/pipeline/context.py` | Re-exports PipelineContext for convenience | DONE |

**Files importing from old path:** Zero stale imports remain. Old docstring references in `core/step.py` and `core/domain/step.py` fixed.

### 1d. `lyrics/` → `core/lyrics/` — Phase 3

| File | Old path | New path | Import changes | Status |
|---|---|---|---|---|
| `core/lyrics/__init__.py` | `lyrics/__init__.py` | `core/lyrics/__init__.py` | `tetodl.lyrics` → `tetodl.core.lyrics` | PENDING |
| `core/lyrics/engine.py` | `lyrics/engine.py` | `core/lyrics/engine.py` | Same | PENDING |
| `core/lyrics/matcher.py` | `lyrics/matcher.py` | `core/lyrics/matcher.py` | Same | PENDING |
| `core/lyrics/models.py` | `lyrics/models.py` | `core/lyrics/models.py` | Same | PENDING |
| `core/lyrics/headers.py` | `lyrics/headers.py` | `core/lyrics/headers.py` | Same | PENDING |
| `core/pipeline/cleaners/title.py` | `lyrics/cleaner.py` | `core/pipeline/cleaners/title.py` | Moves to pipeline (not lyrics) | PENDING |
| `core/lyrics/providers/base.py` | `lyrics/providers/base.py` | `core/lyrics/providers/base.py` | Same | PENDING |
| `core/lyrics/providers/lrclib.py` | `lyrics/providers/lrclib.py` | `core/lyrics/providers/lrclib.py` | Same | PENDING |
| `core/lyrics/providers/genius.py` | `lyrics/providers/genius.py` | `core/lyrics/providers/genius.py` | Same | PENDING |
| `core/lyrics/providers/itunes.py` | `lyrics/providers/itunes.py` | `core/lyrics/providers/itunes.py` | Same | PENDING |

**Files importing from old path:**
```bash
grep -r "tetodl.lyrics" tetodl/ --include="*.py"
```

### 1e. `extractors/` → `core/sources/` — Phase 4

| File | Old path | New path | Import changes | Status |
|---|---|---|---|---|
| `core/sources/__init__.py` | `extractors/__init__.py` | `core/sources/__init__.py` | `tetodl.extractors` → `tetodl.core.sources` | PENDING |
| `core/sources/youtube.py` | `extractors/youtube.py` | `core/sources/youtube.py` | Same | PENDING |
| `core/sources/spotify.py` | `extractors/spotify.py` | `core/sources/spotify.py` | Same | PENDING |
| `core/sources/search.py` | `extractors/search.py` | `core/sources/search.py` | Same | PENDING |
| `core/sources/base.py` | (new file) | `core/sources/base.py` | VideoInfo + SourceHandler protocol | PENDING |

**Files importing from old path:**
```bash
grep -r "tetodl.extractors" tetodl/ --include="*.py"
```

### 1f. `core/spotify/` → `core/clients/spotify/` — Phase 5

| File | Old path | New path | Import changes | Status |
|---|---|---|---|---|
| `core/clients/spotify/__init__.py` | `core/spotify/__init__.py` | `core/clients/spotify/__init__.py` | `tetodl.core.spotify` → `tetodl.core.clients.spotify` | PENDING |
| `core/clients/spotify/client.py` | `core/spotify/client.py` | `core/clients/spotify/client.py` | Same | PENDING |
| `core/clients/spotify/auth.py` | `core/spotify/auth.py` | `core/clients/spotify/auth.py` | Same | PENDING |
| `core/clients/spotify/models.py` | `core/spotify/models.py` | `core/clients/spotify/models.py` | Same | PENDING |
| `core/clients/spotify/ratelimit.py` | `core/spotify/ratelimit.py` | `core/clients/spotify/ratelimit.py` | Same | PENDING |
| `core/clients/spotify/errors.py` | `core/spotify/errors.py` | `core/clients/spotify/errors.py` | Same | PENDING |

**Files importing from old path:**
```bash
grep -r "tetodl.core.spotify" tetodl/ --include="*.py"
```

### 1g. Consolidate into `ui/` umbrella — Phase 6

| File | Old path | New path | Import changes | Status |
|---|---|---|---|---|
| `ui/cli/__init__.py` | `cli/__init__.py` | `ui/cli/__init__.py` | `tetodl.cli` → `tetodl.ui.cli` | PENDING |
| `ui/cli/parser.py` | `cli/parser.py` | `ui/cli/parser.py` | Same | PENDING |
| `ui/cli/dispatch.py` | `cli/dispatch.py` | `ui/cli/dispatch.py` | Same | PENDING |
| `ui/cli/network.py` | *(extract from `utils/network.py`)* | `ui/cli/network.py` | New — `start_share_server` extracted | PENDING |
| `ui/daemon/api.py` | `daemon/api.py` | `ui/daemon/api.py` | `tetodl.daemon` → `tetodl.ui.daemon` | PENDING |
| `ui/daemon/display.py` | `daemon/display.py` | `ui/daemon/display.py` | Same | PENDING |
| `ui/daemon/models.py` | `daemon/models.py` | `ui/daemon/models.py` | Same | PENDING |
| `ui/daemon/service.py` | `daemon/service.py` | `ui/daemon/service.py` | Same | PENDING |
| `ui/daemon/static/index.html` | `daemon/static/index.html` | `ui/daemon/static/index.html` | Update path ref | PENDING |
| `ui/tui/about.py` | `ui/about.py` | `ui/tui/about.py` | `tetodl.ui.about` → `tetodl.ui.tui.about` | PENDING |
| `ui/tui/analytics.py` | `ui/analytics.py` | `ui/tui/analytics.py` | Same | PENDING |
| `ui/tui/components.py` | `ui/components.py` | `ui/tui/components.py` | Same | PENDING |
| `ui/tui/navigation.py` | `ui/navigation.py` | `ui/tui/navigation.py` | Same | PENDING |
| `ui/tui/provider.py` | `ui/provider.py` | `ui/tui/provider.py` | Same | PENDING |
| `ui/tui/settings.py` | `ui/settings.py` | `ui/tui/settings.py` | Same | PENDING |
| `ui/tui/verifier.py` | `ui/verifier.py` | `ui/tui/verifier.py` | Same | PENDING |
| `ui/tui/bootstrap.py` | `ui/entry/bootstrap.py` | `ui/tui/bootstrap.py` | Same | PENDING |
| `ui/tui/menu.py` | `ui/entry/menu.py` | `ui/tui/menu.py` | Same | PENDING |
| `ui/tui/runner.py` | `ui/entry/app.py` | `ui/tui/runner.py` | Move + rename (app → runner) | PENDING |
| `ui/app.py` | *(new)* | `ui/app.py` | Create — neutral orchestrator | PENDING |
| `ui/bootstrap.py` | *(new)* | `ui/bootstrap.py` | Create — startup logic | PENDING |
| `ui/share.py` | `utils/share.py` | `ui/share.py` | `tetodl.utils.share` → `tetodl.ui.share` | PENDING |
| `ui/static/styles.css` | `utils/share_static/styles.css` | `ui/static/styles.css` | Update path refs | PENDING |
| `ui/static/player.js` | `utils/share_static/player.js` | `ui/static/player.js` | Update path refs | PENDING |

**Files importing from old path:**
```bash
grep -r "tetodl.daemon\|tetodl.ui" tetodl/ --include="*.py"
```

### 1h. Share feature — moves with Phase 6

| File | Old path | New path | Import changes | Status |
|---|---|---|---|---|
| `ui/share.py` | `utils/share.py` | `ui/share.py` | `tetodl.utils.share` → `tetodl.ui.share` | PENDING |
| `ui/static/styles.css` | `utils/share_static/styles.css` | `ui/static/styles.css` | Update path refs | PENDING |
| `ui/static/player.js` | `utils/share_static/player.js` | `ui/static/player.js` | Update path refs | PENDING |
| `ui/daemon/static/index.html` | `daemon/static/index.html` | `ui/daemon/static/index.html` | Update path refs | PENDING |

**Files importing share:**
```bash
grep -r "tetodl.utils.share\|utils.share\|share_static" tetodl/ --include="*.py"
```

### 1i. `utils/` — Phase 7 (violation fixes, no moves)

| File | Violation | Fix | Status |
|---|---|---|---|
| `utils/console.py` | Imports `core.cover`, `core.search`, `core.music_brainz`, `core.spotify`, `core.webshare` | Parameterize or move to ui/ | PENDING |
| `utils/display.py` | Imports `core.cache`, `core.config` | Pass config/cache as params | PENDING |
| `utils/files.py` | Check for core imports | Remove if any | PENDING |
| `utils/metadata.py` | Imports `core.smart_cover`, `core.cover`, `core.search` | Parameterize | PENDING |
| `utils/process.py` | Imports `core.smart_cover` | Parameterize | PENDING |
| `utils/io.py` | Imports `core.cover`, `core.smart_cover` | Parameterize | PENDING |
| `utils/path.py` | Imports `core.cover` | Parameterize | PENDING |
| `utils/validate.py` | Imports `core.spotify` | Parameterize | PENDING |

---

## 2. Duplicate Helper Consolidation Tracker

From REFACTOR.md Sections 4+6. Independent of architecture — pure code cleanup.

| Helper | Source (duplicates) | Target | Files to update | Status |
|---|---|---|---|---|
| `clean_title()` | `deezer.py`, `itunes.py`, `genius.py` (3x) | `utils/text_cleaner.py` | 4 files | PENDING |
| `normalize_text()` + `normalize_line()` | `matcher.py` (2 variants) | `utils/text_cleaner.py` | 1 file (matcher.py) | PENDING |
| `has_non_alphabet()` | `matcher.py` | `utils/text_cleaner.py` | 1 file (matcher.py) | PENDING |
| `resolve_artist_title()` | `pipeline/steps/cover.py` + `pipeline/steps/lyrics.py` | `utils/metadata.py` | 2 files | PENDING |
| `human_size()` | `daemon/api.py` + `utils/share.py` | `utils/formatters.py` | 2 files | PENDING |
| `icon_for_ext()` | `daemon/api.py` (_icon) + `utils/share.py` (_classify) | `utils/formatters.py` | 2 files | PENDING |
| `_is_valid_match` (private) | `lyrics/providers/itunes.py` | Replace w/ `matcher.is_valid_match()` | 1 file | PENDING |

---

## 3. Phase Checklist

### Phase 0: Create `core/domain/` + `core/domain/exceptions.py`
- [x] Create `core/domain/__init__.py`
- [x] Move `core/models.py` → `core/domain/models.py` (old stub re-exports from domain)
- [x] Move `core/config.py` → `core/domain/config.py` (old stub re-exports from domain)
- [x] Move `core/cache.py` → `core/domain/cache.py` (old stub re-exports from domain)
- [x] Move `core/history.py` → `core/domain/history.py` (old stub re-exports from domain)
- [x] Move `core/tagger.py` → `core/domain/tagger.py` (old stub re-exports from domain)
- [x] Move `core/registry.py` → `core/domain/registry.py` (old stub re-exports from domain)
- [x] Move `core/step.py` → `core/domain/step.py` (old stub re-exports from domain)
- [x] Move `core/env.py` → `core/domain/env.py`
- [x] Create `core/domain/exceptions.py`
- [x] Create `core/domain/provider.py` (UIProvider + NullUI domain abstraction)
- [x] Update all imports referencing old paths
- [x] Fix `core/domain/env.py`: removed duplicate wsl override type declarations
- [x] Fix `core/dependency.py`: add `Path` import, replace `YTDLP_OVERRIDE_DIR` with `env.get()`
- [x] Fix `utils/network.py`: add missing `shutil` import
- [x] Fix old stubs to re-export from domain (prevent stripped-constant import errors)
- [x] Verify: `grep -r "from tetodl.core\.\(config\|cache\|history\|tagger\|registry\|step\|env\)"` → only docstrings remain
- [x] Run: `python3 -c "import tetodl"` → OK
- [x] Run: `python3 -m tetodl --help` → OK

### Phase 1: Move `services/cover/` → `core/cover/`
- [x] Move all files from `services/cover/` to `core/cover/`
- [x] Update imports: `tetodl.services.cover` → `tetodl.core.cover`
- [x] Delete `services/` if empty
- [x] Verify + test

### Phase 2: Move `pipeline/` → `core/pipeline/`
- [x] Move `pipeline/pipeline.py` → `core/pipeline/runner.py` (rename!)
- [x] Move `pipeline/steps/` → `core/pipeline/stages/` (rename!)
- [x] Move `pipeline/handlers.py` → `core/pipeline/handlers.py`
- [x] Create `core/pipeline/context.py` (re-exports PipelineContext)
- [x] Create `core/pipeline/__init__.py`
- [x] Update ALL imports: `tetodl.pipeline` → `tetodl.core.pipeline`, `steps` → `stages`
- [x] Fixed stale `constants` refs → `env.get(...)` in download.py
- [x] Fixed UI import: uses `core/domain/provider.py` instead of direct `ui/` import
- [x] Fix docstring references in `core/step.py` and `core/domain/step.py`
- [x] Verify: `grep -r "tetodl.pipeline" tetodl/` → zero results
- [x] Verify: `grep -r "tetodl.extractors\|tetodl.lyrics\|tetodl.services\|tetodl.daemon" tetodl/` → zero results
- [x] Run: `python3 -c "import tetodl"` → OK
- [x] Run: `python3 -m tetodl --help` → OK

### Phase 3: Move `lyrics/` → `core/lyrics/` + `core/pipeline/cleaners/`
- [x] Move `lyrics/engine.py`, `matcher.py`, `models.py`, `headers.py` → `core/lyrics/`
- [x] Move `lyrics/providers/` → `core/lyrics/providers/`
- [x] Move `lyrics/cleaner.py` → `core/pipeline/cleaners/title.py`
- [x] Create `core/pipeline/cleaners/__init__.py`
- [x] Update imports: `tetodl.lyrics` → `tetodl.core.lyrics`
- [x] Update cleaner import: `tetodl.lyrics.cleaner` → `tetodl.core.pipeline.cleaners.title`
- [x] Delete `lyrics/` if empty
- [x] Verify + test

### Phase 4: Move `extractors/` → `core/sources/`
- [x] Create `core/sources/__init__.py`
- [x] Create `core/sources/base.py` (new — SourceHandler protocol)
- [x] Move `extractors/youtube.py` → `core/sources/youtube.py`
- [x] Move `extractors/spotify.py` → `core/sources/spotify.py`
- [x] Move `extractors/search.py` → `core/sources/search.py`
- [x] Update imports: `tetodl.extractors` → `tetodl.core.sources`
- [x] Delete `extractors/` if empty
- [x] Verify + test

### Phase 5: Move `core/spotify/` → `core/clients/spotify/`
- [x] Create `core/clients/__init__.py`
- [x] Create `core/clients/spotify/__init__.py`
- [x] Move all files from `core/spotify/` to `core/clients/spotify/`
- [x] Update imports: `tetodl.core.spotify` → `tetodl.core.clients.spotify`
- [x] Delete `core/spotify/` if empty
- [x] Verify + test

### Phase 6: Consolidate into `ui/` umbrella (cli/ → ui/cli/, daemon/ → ui/daemon/, tui/ flat, share/static)
- [x] Create `ui/app.py` — neutral orchestrator
- [x] Create `ui/bootstrap.py` — startup logic
- [x] Move `cli/parser.py`, `cli/dispatch.py`, `cli/__init__.py` → `ui/cli/`
- [x] Extract `start_share_server` from `utils/network.py` → `ui/cli/network.py`
- [x] Move `daemon/` files → `ui/daemon/`
- [x] Move `daemon/static/index.html` → `ui/daemon/static/index.html`
- [x] Move `ui/about.py`, `ui/analytics.py`, `ui/components.py`, `ui/navigation.py`, `ui/provider.py`, `ui/settings.py`, `ui/verifier.py` → `ui/tui/`
- [x] Move `ui/entry/app.py` → `ui/tui/runner.py` (rename)
- [x] Move `ui/entry/bootstrap.py` → `ui/tui/bootstrap.py`
- [x] Move `ui/entry/menu.py` → `ui/tui/menu.py`
- [x] Move `utils/share.py` → `ui/share.py`
- [x] Move `utils/share_static/` → `ui/static/`
- [x] Update all import paths (`tetodl.cli` → `tetodl.ui.cli`, `tetodl.daemon` → `tetodl.ui.daemon`, `tetodl.ui.about` → `tetodl.ui.tui.about`, etc.)
- [x] Fix `_STATIC_DIR` path in `ui/share.py`: `share_static` → `static`
- [x] Delete `cli/`, `daemon/`, `utils/share.py`, `utils/share_static/` if empty — all gone
- [x] Verify + test

### Phase 7: Fix `utils/` layer violations
- [x] Verified: zero `from tetodl.core.*` or `from tetodl.ui.*` imports in any `utils/` file (only intra-`utils` imports exist)
- [x] Move `locales/en.json` → `utils/locales/en.json`
- [x] Move `locales/id.json` → `utils/locales/id.json`
- [x] Update `utils/i18n.py` locale path
- [x] Verify: `grep -r "from tetodl\.\(core\|cli\|pipeline\|lyrics\|extractors\|services\|daemon\|ui\)" tetodl/utils/` → zero matches

### Helper Consolidation (independent, do in parallel w/ any phase)
- [x] Create `utils/text_cleaner.py` (clean_title, normalize_text, normalize_line, has_non_alphabet, get_search_queries)
- [x] Update `core/cover/providers/deezer.py` → import clean_title (removed local _clean_title)
- [x] Update `core/lyrics/providers/genius.py` → import clean_title + get_search_queries (removed locals)
- [x] Update `core/cover/providers/genius.py` → import clean_title + get_search_queries (removed locals)
- [x] Update `core/lyrics/matcher.py` → import normalize_text, normalize_line, has_non_alphabet (removed locals)
- [x] Create `core/pipeline/metadata.py` with resolve_artist_title (merged priority chain)
- [x] Update `core/pipeline/stages/cover.py` → import resolve_artist_title (removed local _resolve_artist_title)
- [x] Update `core/pipeline/stages/lyrics.py` → import resolve_artist_title (removed local _resolve_search_terms)
- [x] Add human_size() + icon_for_ext() to `utils/formatters.py`
- [x] Update `ui/share.py` → import human_size, icon_for_ext, extension sets (removed local _human_size, _classify, sets)
- [x] Update `ui/daemon/api.py` → import human_size, icon_for_ext (removed local _icon, _size_str, AUDIO_EXTS/VIDEO_EXTS)
- [x] Verify: `is_valid_match` already public in matcher.py; all providers (itunes, deezer, genius, cover/providers/genius) use public import
- [x] Verify + test: import tetodl, --help, daemon, share all OK

---

## 4. Verification Commands

Run after EACH phase:

```bash
# 1. Core import check — no ImportError
python3 -c "import tetodl; print('IMPORT OK')"

# 2. CLI entry works
python3 -m tetodl --help

# 3. All tests pass
python3 -m pytest tetodl/tests/ -x --timeout=60 --tb=short 2>&1 | tail -30

# 4. No stale imports
for pkg in pipeline extractors lyrics services daemon ui; do
  result=$(grep -r "from tetodl\.$pkg\." tetodl/ 2>/dev/null | grep -v "tests/\|\.pyc\|__pycache__" | head -5)
  if [ -n "$result" ]; then echo "❌ STALE: $pkg"; echo "$result"; else echo "✅ $pkg clean"; fi
done

# 5. utils purity
violations=$(grep -r "from tetodl\.\(core\|cli\|pipeline\|lyrics\|extractors\|services\|daemon\|ui\)" tetodl/utils/ --include="*.py" 2>/dev/null | head -10)
if [ -n "$violations" ]; then echo "❌ utils VIOLATIONS:"; echo "$violations"; else echo "✅ utils pure"; fi

# 6. core → ui isolation
core_to_ui=$(grep -r "from tetodl\.ui" tetodl/core/ --include="*.py" 2>/dev/null | head -5)
if [ -n "$core_to_ui" ]; then echo "❌ core→ui:"; echo "$core_to_ui"; else echo "✅ core isolated from ui"; fi
```
