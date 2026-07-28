# REFACTOR TRACKER — 3-Layer Architecture Migration

> **Branch:** `refactor/restructure`
> **Base:** `main` (73a5095)
> **Goal:** Transform `tetodl/` into 3 clean layers (`cli/`, `core/`, `utils/`).

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
| `core/pipeline/__init__.py` | `pipeline/__init__.py` | `core/pipeline/__init__.py` | `tetodl.pipeline` → `tetodl.core.pipeline` | PENDING |
| `core/pipeline/runner.py` | `pipeline/pipeline.py` | `core/pipeline/runner.py` | Same + rename | PENDING |
| `core/pipeline/handlers.py` | `pipeline/handlers.py` | `core/pipeline/handlers.py` | Same | PENDING |
| `core/pipeline/stages/classify.py` | `pipeline/steps/classify.py` | `core/pipeline/stages/classify.py` | Same + rename | PENDING |
| `core/pipeline/stages/cover.py` | `pipeline/steps/cover.py` | `core/pipeline/stages/cover.py` | Same + rename | PENDING |
| `core/pipeline/stages/download.py` | `pipeline/steps/download.py` | `core/pipeline/stages/download.py` | Same + rename | PENDING |
| `core/pipeline/stages/extract.py` | `pipeline/steps/extract.py` | `core/pipeline/stages/extract.py` | Same + rename | PENDING |
| `core/pipeline/stages/finalize.py` | `pipeline/steps/finalize.py` | `core/pipeline/stages/finalize.py` | Same + rename | PENDING |
| `core/pipeline/stages/lyrics.py` | `pipeline/steps/lyrics.py` | `core/pipeline/stages/lyrics.py` | Same + rename | PENDING |

**Files importing from old path:**
```bash
grep -r "tetodl.pipeline" tetodl/ --include="*.py"
# → cli/dispatch.py, core/step.py, tests/pipeline/, etc.
```

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

### 1g. `daemon/` → `cli/daemon/` + `ui/` → `cli/tui/` — Phase 6

| File | Old path | New path | Import changes | Status |
|---|---|---|---|---|
| `cli/daemon/api.py` | `daemon/api.py` | `cli/daemon/api.py` | `tetodl.daemon` → `tetodl.cli.daemon` | PENDING |
| `cli/daemon/display.py` | `daemon/display.py` | `cli/daemon/display.py` | Same | PENDING |
| `cli/daemon/models.py` | `daemon/models.py` | `cli/daemon/models.py` | Same | PENDING |
| `cli/daemon/service.py` | `daemon/service.py` | `cli/daemon/service.py` | Same | PENDING |
| `cli/tui/about.py` | `ui/about.py` | `cli/tui/about.py` | `tetodl.ui` → `tetodl.cli.tui` | PENDING |
| `cli/tui/analytics.py` | `ui/analytics.py` | `cli/tui/analytics.py` | Same | PENDING |
| `cli/tui/components.py` | `ui/components.py` | `cli/tui/components.py` | Same | PENDING |
| `cli/tui/navigation.py` | `ui/navigation.py` | `cli/tui/navigation.py` | Same | PENDING |
| `cli/tui/provider.py` | `ui/provider.py` | `cli/tui/provider.py` | Same | PENDING |
| `cli/tui/settings.py` | `ui/settings.py` | `cli/tui/settings.py` | Same | PENDING |
| `cli/tui/verifier.py` | `ui/verifier.py` | `cli/tui/verifier.py` | Same | PENDING |
| `cli/tui/entry/app.py` | `ui/entry/app.py` | `cli/tui/entry/app.py` | Same | PENDING |
| `cli/tui/entry/bootstrap.py` | `ui/entry/bootstrap.py` | `cli/tui/entry/bootstrap.py` | Same | PENDING |
| `cli/tui/entry/menu.py` | `ui/entry/menu.py` | `cli/tui/entry/menu.py` | Same | PENDING |

**Files importing from old path:**
```bash
grep -r "tetodl.daemon\|tetodl.ui" tetodl/ --include="*.py"
```

### 1h. Share feature — moves with Phase 6

| File | Old path | New path | Import changes | Status |
|---|---|---|---|---|
| `cli/share.py` | `utils/share.py` | `cli/share.py` | `tetodl.utils.share` → `tetodl.cli.share` | PENDING |
| `cli/static/styles.css` | `utils/share_static/styles.css` | `cli/static/styles.css` | Update path refs | PENDING |
| `cli/static/player.js` | `utils/share_static/player.js` | `cli/static/player.js` | Update path refs | PENDING |
| `cli/daemon/static/index.html` | `daemon/static/index.html` | `cli/daemon/static/index.html` | Update path refs | PENDING |

**Files importing share:**
```bash
grep -r "tetodl.utils.share\|utils.share\|share_static" tetodl/ --include="*.py"
```

### 1i. `utils/` — Phase 7 (violation fixes, no moves)

| File | Violation | Fix | Status |
|---|---|---|---|
| `utils/console.py` | Imports `core.cover`, `core.search`, `core.music_brainz`, `core.spotify`, `core.webshare` | Parameterize or move to cli/ | PENDING |
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
- [ ] Create `core/domain/__init__.py`
- [ ] Move `core/models.py` → `core/domain/models.py`
- [ ] Move `core/config.py` → `core/domain/config.py`
- [ ] Move `core/cache.py` → `core/domain/cache.py`
- [ ] Move `core/history.py` → `core/domain/history.py`
- [ ] Move `core/tagger.py` → `core/domain/tagger.py`
- [ ] Move `core/registry.py` → `core/domain/registry.py`
- [ ] Move `core/step.py` → `core/domain/step.py`
- [ ] Move `core/env.py` → `core/domain/env.py`
- [ ] Create `core/domain/exceptions.py`
- [ ] Update all imports referencing old paths
- [ ] Verify: `grep -r "from tetodl.core\.\(config\|cache\|history\|tagger\|registry\|step\|env\)"` → update them all
- [ ] Run: `python3 -c "import tetodl"` → no ImportError
- [ ] Run: `python3 -m pytest tetodl/tests/ -x --timeout=60`

### Phase 1: Move `services/cover/` → `core/cover/`
- [ ] Move all files from `services/cover/` to `core/cover/`
- [ ] Update imports: `tetodl.services.cover` → `tetodl.core.cover`
- [ ] Delete `services/` if empty
- [ ] Verify + test

### Phase 2: Move `pipeline/` → `core/pipeline/`
- [ ] Move `pipeline/pipeline.py` → `core/pipeline/runner.py` (rename!)
- [ ] Move `pipeline/steps/` → `core/pipeline/stages/` (rename!)
- [ ] Move `pipeline/handlers.py` → `core/pipeline/handlers.py`
- [ ] Move `pipeline/__init__.py` → `core/pipeline/__init__.py`
- [ ] Update ALL imports: `tetodl.pipeline` → `tetodl.core.pipeline`, `steps` → `stages`
- [ ] Delete `pipeline/` if empty
- [ ] Verify + test

### Phase 3: Move `lyrics/` → `core/lyrics/` + `core/pipeline/cleaners/`
- [ ] Move `lyrics/engine.py`, `matcher.py`, `models.py`, `headers.py` → `core/lyrics/`
- [ ] Move `lyrics/providers/` → `core/lyrics/providers/`
- [ ] Move `lyrics/cleaner.py` → `core/pipeline/cleaners/title.py`
- [ ] Create `core/pipeline/cleaners/__init__.py`
- [ ] Update imports: `tetodl.lyrics` → `tetodl.core.lyrics`
- [ ] Update cleaner import: `tetodl.lyrics.cleaner` → `tetodl.core.pipeline.cleaners.title`
- [ ] Delete `lyrics/` if empty
- [ ] Verify + test

### Phase 4: Move `extractors/` → `core/sources/`
- [ ] Create `core/sources/__init__.py`
- [ ] Create `core/sources/base.py` (new — SourceHandler protocol)
- [ ] Move `extractors/youtube.py` → `core/sources/youtube.py`
- [ ] Move `extractors/spotify.py` → `core/sources/spotify.py`
- [ ] Move `extractors/search.py` → `core/sources/search.py`
- [ ] Update imports: `tetodl.extractors` → `tetodl.core.sources`
- [ ] Delete `extractors/` if empty
- [ ] Verify + test

### Phase 5: Move `core/spotify/` → `core/clients/spotify/`
- [ ] Create `core/clients/__init__.py`
- [ ] Create `core/clients/spotify/__init__.py`
- [ ] Move all files from `core/spotify/` to `core/clients/spotify/`
- [ ] Update imports: `tetodl.core.spotify` → `tetodl.core.clients.spotify`
- [ ] Delete `core/spotify/` if empty
- [ ] Add `core/clients/music_brainz.py`, `core/clients/webshare.py` (if they exist as separate modules)
- [ ] Verify + test

### Phase 6: Merge `daemon/` + `ui/` into `cli/`
- [ ] Create `cli/daemon/`
- [ ] Move `daemon/` files → `cli/daemon/`
- [ ] Move `daemon/static/index.html` → `cli/daemon/static/index.html`
- [ ] Create `cli/tui/`
- [ ] Move `ui/` files → `cli/tui/`
- [ ] Move `ui/entry/` → `cli/tui/entry/`
- [ ] Move `utils/share.py` → `cli/share.py`
- [ ] Move `utils/share_static/` → `cli/static/`
- [ ] Update all import paths
- [ ] Delete `daemon/`, `ui/` if empty
- [ ] Verify + test

### Phase 7: Fix `utils/` layer violations
- [ ] `utils/console.py` — remove all `from tetodl.core.*` imports
- [ ] `utils/display.py` — parameterize cache/config
- [ ] `utils/metadata.py` — parameterize cover/search
- [ ] `utils/process.py` — parameterize smart_cover
- [ ] `utils/io.py` — parameterize cover/smart_cover
- [ ] `utils/path.py` — parameterize cover
- [ ] `utils/validate.py` — parameterize spotify
- [ ] Move `locales/en.json` → `utils/locales/en.json`
- [ ] Move `locales/id.json` → `utils/locales/id.json`
- [ ] Update `utils/i18n.py` locale path
- [ ] Verify: `grep -r "from tetodl\.\(core\|cli\|pipeline\|lyrics\|extractors\|services\|daemon\|ui\)" tetodl/utils/` → zero matches
- [ ] Verify + test

### Helper Consolidation (independent, do in parallel w/ any phase)
- [ ] Create `utils/text_cleaner.py` (clean_title, normalize_text, normalize_line, has_non_alphabet)
- [ ] Update 4 callers to import from text_cleaner
- [ ] Create `utils/metadata.py` (resolve_artist_title)
- [ ] Update 2 callers to import from metadata
- [ ] Add human_size() + icon_for_ext() to `utils/formatters.py`
- [ ] Update 2 callers (daemon/api.py, utils/share.py → cli/share.py)
- [ ] Replace private `_is_valid_match` in `itunes.py` with public from `matcher.py`
- [ ] Verify + test

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

# 6. core → cli isolation
core_to_cli=$(grep -r "from tetodl\.cli" tetodl/core/ --include="*.py" 2>/dev/null | head -5)
if [ -n "$core_to_cli" ]; then echo "❌ core→cli:"; echo "$core_to_cli"; else echo "✅ core isolated"; fi
```
