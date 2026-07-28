# TetoDL 3-Layer Refactor Plan (Alternative)

> **Why this exists:** The original `plan/REFACTOR.md` proposed 4 layers (`core/`, `services/`, `utils/`, `ui/`). After deeper analysis, that split has fundamental problems. This document proposes a cleaner 3-layer architecture (`cli/`, `core/`, `utils/`) and maps every file to its new home.

---

## Table of Contents

1. [Why 4-Layer Failed — Comparison Matrix](#1-why-4-layer-failed--comparison-matrix)
2. [Target Architecture: 3 Layers](#2-target-architecture-3-layers)
3. [Complete File Migration Map](#3-complete-file-migration-map)
4. [New Structure in Detail](#4-new-structure-in-detail)
5. [Dependency Rules](#5-dependency-rules)
6. [SOLID & Design Patterns](#6-solid--design-patterns)
7. [File Size Budget](#7-file-size-budget)
8. [Migration Phases](#8-migration-phases)
9. [Risk Matrix](#9-risk-matrix)
10. [Verification Plan](#10-verification-plan)
11. [Static Assets & Share Feature](#11-static-assets--share-feature)
12. [Redundant Helper Consolidation](#12-redundant-helper-consolidation)
13. [Import Tracking & Git Workflow](#13-import-tracking--git-workflow)

---

## 1. Why 4-Layer Failed — Comparison Matrix

The 4-layer plan (`utils/` → `core/` → `services/` → `ui/`) was the starting point, but it introduces artificial boundaries that hurt readability and maintainability.

| Dimension | Current (monolith) | REFACTOR.md (4-layer) | REFACTOR_ALT.md (3-layer) |
|---|---|---|---|
| **Top-level dirs** | 11 (`core`, `utils`, `cli`, `daemon`, `ui`, `pipeline`, `lyrics`, `extractors`, `services`, `locales`, `tests`) | 4 (`core`, `services`, `utils`, `ui`) | **3** (`cli`, `core`, `utils`) |
| **Related code split across layers** | Mild (lyrics in `lyrics/`, cover in `services/cover/`) | **Severe** (pipeline steps in `core/pipeline/steps/`, cover providers in `services/cover/providers/`, lyrics providers in `services/lyrics/providers/`) | **None** — all pipeline logic in `core/pipeline/`, all clients in `core/clients/` |
| **`core/` vs `services/` boundary** | N/A (not yet split) | **Arbitrary.** Why is `core/spotify/` in "core" but `services/extractors/` in "services"? Why is `core/pipeline/steps/download.py` in "core" but `services/lyrics/` in "services"? No clear rule. | **Absent.** One `core/` layer for all business logic. No false distinction. |
| **Mental model match** | ✗ Scattered | ✗ Split by vague "importance" | ✓ **Maps to data flow:** sources (branch) → pipeline (merge) |
| **Newcomer findability** | "Where is Spotify login?" → could be 3 places | "Where is cover logic?" → `services/cover/providers/` or `core/pipeline/steps/cover.py` | "Where is Spotify client?" → `core/clients/spotify/` ✅ |
| **`utils/` violations** | 9 files leak into `core/` | **Still 9 files leak** (Phase 4 only fixes `thumbnail.py` and `display.py`) | **Zero** — utils is enforced pure |
| **Testability** | Low (global state, console.err everywhere) | Medium (exceptions added in Phase 5, but services layer still mixed) | **High** — every client injectable, pipeline stages take context, console.err only in `cli/` |
| **Scalability — new source (Deezer)** | Add file somewhere... | `services/extractors/deezer.py`? Or `core/`? Or new top-level? | `core/sources/deezer.py` ✅ **unambiguous** |
| **Scalability — new API client** | Add to `lyrics/providers/` or `services/cover/providers/` | `services/lyrics/providers/` or `services/cover/providers/` | `core/clients/` ✅ **single location** |
| **Pipeline stage reuse** | Pipeline steps import from `lyrics/`, `services/cover/`, `core/` — tangled | A pipeline step imports from `services/lyrics/`, `services/cover/` — still split | A pipeline step imports from `core/clients/` and `core/` root — **single source** |
| **Risk of size blowup** | Some files 400+ lines | Some services files 300+ lines | **Monitored** — each file capped at ~300 lines, split when exceeded |

### Root cause of 4-layer failure

The `services/` layer tries to separate "external API clients" from "internal domain logic", but in practice:
- External API clients (Spotify, Genius, LRCLib) need domain models from `core/`
- Domain orchestrators (pipeline stages) need to call external API clients
- The result: **everything imports from everything anyway**, the layer boundary adds no real decoupling, just directory navigation overhead

**3-layer solves this:** There is no `services/`. API clients live in `core/clients/`. Orchestrators live in `core/pipeline/stages/`. No ambiguity.

---

## 2. Target Architecture: 3 Layers

```
tetodl/
├── __init__.py
├── __main__.py
├── constants.py              ← semua layer boleh import (APP_VERSION, enums, dll)
│
├── cli/                      ← PRESENTATION — depends on core/ + utils/
│   ├── commands/             ← Thin command handlers (download, search, config)
│   │   ├── download.py
│   │   ├── search.py
│   │   └── config.py
│   ├── daemon/               ← HTTP API server
│   │   ├── api.py
│   │   ├── display.py
│   │   ├── models.py
│   │   └── service.py
│   ├── tui/                  ← Textual TUI components
│   │   ├── about.py
│   │   ├── analytics.py
│   │   ├── components.py
│   │   ├── navigation.py
│   │   ├── provider.py
│   │   ├── settings.py
│   │   └── verifier.py
│   ├── parser.py             ← Cement CLI argument parser
│   ├── dispatch.py           ← Command dispatcher
│   └── utils.py              ← CLI-specific helpers (formatting, rendering)
│
├── core/                     ← BUSINESS LOGIC — depends on utils/ only
│   ├── sources/              ← BRANCHING: input URL → list of VideoInfo
│   │   ├── base.py           ← Abstract SourceHandler protocol
│   │   ├── youtube.py        ← YouTube + YouTube Music (single, playlist, album)
│   │   └── spotify.py        ← Spotify → resolve to YouTube search
│   │
│   ├── pipeline/             ← MERGED: process VideoInfo → completed file
│   │   ├── context.py        ← PipelineContext dataclass + VideoInfo
│   │   ├── runner.py         ← Pipeline orchestrator
│   │   ├── handlers.py       ← Error handlers, callbacks
│   │   ├── stages/
│   │   │   ├── classify.py   ← URL type detection
│   │   │   ├── extract.py    ← yt-dlp info extraction
│   │   │   ├── download.py   ← Audio download
│   │   │   ├── lyrics.py     ← Lyrics fetching
│   │   │   ├── cover.py      ← Cover image download
│   │   │   └── finalize.py   ← FFmpeg metadata embed + file finalization
│   │   └── cleaners/
│   │       └── title.py      ← Title cleaning strategies per-source
│   │
│   ├── lyrics/               ← Lyrics orchestration (engine, matcher, providers)
│   │   ├── engine.py         ← Facade: search_lyrics(artist, title, duration)
│   │   ├── matcher.py        ← Scoring, fuzzy matching, anchor alignment
│   │   ├── models.py         ← LyricsQuery, LyricsData dataclasses
│   │   ├── headers.py        ← User-Agent generation
│   │   └── providers/        ← Strategy pattern
│   │       ├── base.py       ← Abstract LyricsProvider
│   │       ├── lrclib.py     ← LRCLIB API client
│   │       ├── genius.py     ← Genius API + scrape
│   │       └── itunes.py     ← iTunes Search API (metadata + cover fallback)
│   │
│   ├── cover/                ← Cover orchestration (download, process, providers)
│   │   ├── image.py          ← Image download
│   │   ├── models.py         ← CoverResult, CoverMetadata
│   │   ├── processor.py      ← Image crop, convert, format
│   │   └── providers/
│   │       ├── base.py       ← Abstract CoverProvider
│   │       ├── deezer.py     ← Deezer cover API
│   │       ├── itunes.py     ← iTunes cover API
│   │       └── genius.py     ← Genius cover API
│   │
│   ├── clients/              ← Thin external API wrappers (1 file unless complex)
│   │   ├── spotify/          ← Package — OAuth flow is non-trivial
│   │   │   ├── __init__.py
│   │   │   ├── client.py     ← SpotifyClient (public API)
│   │   │   ├── auth.py       ← OAuth token management
│   │   │   ├── models.py     ← SpotifyTrack, SpotifyAlbum, ...
│   │   │   └── ratelimit.py  ← Rate limiting
│   │   ├── music_brainz.py   ← MusicBrainz API (1 file, ~80 lines)
│   │   └── webshare.py       ← Webshare proxy API (1 file, ~50 lines)
│   │
│   ├── domain/               ← Domain models, config, and services
│   │   ├── __init__.py
│   │   ├── models.py         ← DownloadResult, MediaInfo, etc.
│   │   ├── config.py         ← App configuration
│   │   ├── cache.py          ← Caching layer
│   │   ├── history.py        ← Download history
│   │   ├── tagger.py         ← Metadata tagging (FFmpeg)
│   │   ├── registry.py       ← Provider/plugin registry
│   │   ├── step.py           ← Base step interface
│   │   ├── env.py            ← Environment resolver
│   │   └── exceptions.py     ← Generic app exceptions
│   │
│   ├── dependency.py         ← Dependency verification (ffmpeg, yt-dlp)
│   ├── maintenance.py        ← Update/uninstall logic
│   ├── search.py             ← Unified search (core search logic)
│   ├── resolver.py           ← URL resolver
│   └── extractor.py          ← Base extractor logic
│
└── utils/                    ← PURE HELPERS — zero tetodl imports
    ├── console/              ← Logging/error sink
    │   ├── __init__.py
    │   ├── logger.py
    │   ├── contexts.py
    │   └── themes.py
    ├── locales/              ← i18n JSON files
    │   ├── en.json
    │   └── id.json
    ├── files.py              ← File I/O helpers
    ├── path.py               ← Path resolution (no core imports)
    ├── network.py            ← requests session, retry
    ├── formatters.py         ← human_size, icon_for_ext, format helpers
    ├── i18n.py               ← Internationalization
    ├── i18n_keys.py          ← Generated i18n key constants
    ├── time_parser.py        ← Time parsing utilities
    ├── processing.py         ← Common processing helpers
    ├── share.py              ← Sharing utilities
    ├── hooks.py              ← Hook system
    ├── tracer.py             ← Tracing/debug
    ├── media_scanner.py      ← Media file scanning
    └── logger.py             ← Legacy logger (deprecated, migrate to console/)
```

### Structural invariants

| Rule | Detail |
|---|---|
| **`utils/` imports zero tetodl packages** | `from tetodl.*` is **forbidden**. Only stdlib + third-party. |
| **`core/` imports from `utils/` and `constants` only** | No `core/` → `cli/` imports. No `core/` → `core/clients/` → `core/` circular. Wait — `clients/` can import from `core/domain/` (models, exceptions). |
| **`cli/` imports from `core/` and `utils/`** | `cli/` is the composition root. It wires everything together. |
| **No circular imports** | `core/domain/` → `core/clients/` is OK. `core/clients/` → `core/sources/` is NOT (would create cycle). |
| **One file = one responsibility** | Max ~300 lines per file. Split when exceeded. |

---

## 3. Complete File Migration Map

Every `.py` file in the current codebase, and where it goes in the new structure.

### 3a. `core/` — Domain root files (stay in `core/`)

| Current path | New path | Action |
|---|---|---|
| `core/__init__.py` | `core/__init__.py` | Keep (update exports) |
| `core/models.py` | `core/domain/models.py` | Move |
| `core/config.py` | `core/domain/config.py` | Move |
| `core/cache.py` | `core/domain/cache.py` | Move |
| `core/history.py` | `core/domain/history.py` | Move |
| `core/tagger.py` | `core/domain/tagger.py` | Move |
| `core/registry.py` | `core/domain/registry.py` | Move |
| `core/step.py` | `core/domain/step.py` | Move |
| `core/env.py` | `core/domain/env.py` | Move |
| `core/dependency.py` | `core/dependency.py` | Keep at `core/` root |
| `core/maintenance.py` | `core/maintenance.py` | Keep at `core/` root |
| `core/search.py` | `core/search.py` | Keep at `core/` root |
| `core/resolver.py` | `core/resolver.py` | Keep at `core/` root |
| `core/extractor.py` | `core/extractor.py` | Keep at `core/` root |

### 3b. `core/spotify/` → `core/clients/spotify/`

| Current path | New path | Action |
|---|---|---|
| `core/spotify/__init__.py` | `core/clients/spotify/__init__.py` | Move |
| `core/spotify/client.py` | `core/clients/spotify/client.py` | Move |
| `core/spotify/auth.py` | `core/clients/spotify/auth.py` | Move |
| `core/spotify/models.py` | `core/clients/spotify/models.py` | Move |
| `core/spotify/ratelimit.py` | `core/clients/spotify/ratelimit.py` | Move |
| `core/spotify/errors.py` | `core/clients/spotify/errors.py` | Move (or inline into client.py) |

### 3c. `pipeline/` → `core/pipeline/`

| Current path | New path | Action |
|---|---|---|
| `pipeline/__init__.py` | `core/pipeline/__init__.py` | Move |
| `pipeline/pipeline.py` | `core/pipeline/runner.py` | Move + rename |
| `pipeline/handlers.py` | `core/pipeline/handlers.py` | Move |
| `pipeline/steps/classify.py` | `core/pipeline/stages/classify.py` | Move |
| `pipeline/steps/cover.py` | `core/pipeline/stages/cover.py` | Move (may merge with cover logic) |
| `pipeline/steps/download.py` | `core/pipeline/stages/download.py` | Move |
| `pipeline/steps/extract.py` | `core/pipeline/stages/extract.py` | Move |
| `pipeline/steps/finalize.py` | `core/pipeline/stages/finalize.py` | Move |
| `pipeline/steps/lyrics.py` | `core/pipeline/stages/lyrics.py` | Move |

### 3d. `lyrics/` → `core/lyrics/`

| Current path | New path | Action |
|---|---|---|
| `lyrics/__init__.py` | `core/lyrics/__init__.py` | Move |
| `lyrics/engine.py` | `core/lyrics/engine.py` | Move |
| `lyrics/matcher.py` | `core/lyrics/matcher.py` | Move |
| `lyrics/models.py` | `core/lyrics/models.py` | Move |
| `lyrics/headers.py` | `core/lyrics/headers.py` | Move |
| `lyrics/cleaner.py` | `core/pipeline/cleaners/title.py` | Move (title cleaning → pipeline cleaners) |
| `lyrics/providers/base.py` | `core/lyrics/providers/base.py` | Move |
| `lyrics/providers/lrclib.py` | `core/lyrics/providers/lrclib.py` | Move |
| `lyrics/providers/genius.py` | `core/lyrics/providers/genius.py` | Move |
| `lyrics/providers/itunes.py` | `core/lyrics/providers/itunes.py` | Move |

### 3e. `extractors/` → `core/sources/`

| Current path | New path | Action |
|---|---|---|
| `extractors/__init__.py` | `core/sources/__init__.py` | Move |
| `extractors/youtube.py` | `core/sources/youtube.py` | Move |
| `extractors/spotify.py` | `core/sources/spotify.py` | Move |
| `extractors/search.py` | `core/sources/search.py` | Move |

### 3f. `services/cover/` → `core/cover/`

| Current path | New path | Action |
|---|---|---|
| `services/cover/__init__.py` | `core/cover/__init__.py` | Move |
| `services/cover/image.py` | `core/cover/image.py` | Move |
| `services/cover/models.py` | `core/cover/models.py` | Move |
| `services/cover/processor.py` | `core/cover/processor.py` | Move |
| `services/cover/providers/base.py` | `core/cover/providers/base.py` | Move |
| `services/cover/providers/deezer.py` | `core/cover/providers/deezer.py` | Move |
| `services/cover/providers/genius.py` | `core/cover/providers/genius.py` | Move |
| `services/cover/providers/itunes.py` | `core/cover/providers/itunes.py` | Move |
| `services/__init__.py` | *(Delete)* | Removed — services layer dissolved |

### 3g. `cli/` → `cli/` (stays, flattens)

| Current path | New path | Action |
|---|---|---|
| `cli/parser.py` | `cli/parser.py` | Keep |
| `cli/dispatch.py` | `cli/dispatch.py` | Keep |

### 3h. `daemon/` → `cli/daemon/`

| Current path | New path | Action |
|---|---|---|
| `daemon/api.py` | `cli/daemon/api.py` | Move |
| `daemon/display.py` | `cli/daemon/display.py` | Move |
| `daemon/models.py` | `cli/daemon/models.py` | Move |
| `daemon/service.py` | `cli/daemon/service.py` | Move |

### 3i. `ui/` → `cli/tui/`

| Current path | New path | Action |
|---|---|---|
| `ui/__init__.py` | `cli/__init__.py` | Merge (cli/ already has __init__.py) |
| `ui/about.py` | `cli/tui/about.py` | Move |
| `ui/analytics.py` | `cli/tui/analytics.py` | Move |
| `ui/components.py` | `cli/tui/components.py` | Move |
| `ui/navigation.py` | `cli/tui/navigation.py` | Move |
| `ui/provider.py` | `cli/tui/provider.py` | Move |
| `ui/settings.py` | `cli/tui/settings.py` | Move |
| `ui/verifier.py` | `cli/tui/verifier.py` | Move |
| `ui/entry/__init__.py` | `cli/tui/entry/__init__.py` | Move |
| `ui/entry/app.py` | `cli/tui/entry/app.py` | Move |
| `ui/entry/bootstrap.py` | `cli/tui/entry/bootstrap.py` | Move |
| `ui/entry/menu.py` | `cli/tui/entry/menu.py` | Move |

### 3j. `utils/` — mostly stays (some violations need fixing)

| Current path | New path | Action |
|---|---|---|
| `utils/__init__.py` | `utils/__init__.py` | Keep |
| `utils/console/__init__.py` | `utils/console/__init__.py` | Keep |
| `utils/console/logger.py` | `utils/console/logger.py` | Keep |
| `utils/console/contexts.py` | `utils/console/contexts.py` | Keep |
| `utils/console/themes.py` | `utils/console/themes.py` | Keep |
| `utils/display.py` | `utils/display.py` | Keep (after fixing core imports → parameterize) |
| `utils/files.py` | `utils/files.py` | Keep |
| `utils/formatters.py` | `utils/formatters.py` | Keep |
| `utils/hooks.py` | `utils/hooks.py` | Keep |
| `utils/i18n.py` | `utils/i18n.py` | Keep |
| `utils/i18n_keys.py` | `utils/i18n_keys.py` | Keep |
| `utils/logger.py` | `utils/logger.py` | Keep |
| `utils/media_scanner.py` | `utils/media_scanner.py` | Keep |
| `utils/network.py` | `utils/network.py` | Keep |
| `utils/processing.py` | `utils/processing.py` | Keep |
| `utils/share.py` | `utils/share.py` | Keep |
| `utils/time_parser.py` | `utils/time_parser.py` | Keep |
| `utils/tracer.py` | `utils/tracer.py` | Keep |
| `utils/thumbnail.py` | ***(Delete)*** — already superseded by CoverService |
| `locales/en.json` | `utils/locales/en.json` | Move |
| `locales/id.json` | `utils/locales/id.json` | Move |

### 3k. Root files

| Current path | New path | Action |
|---|---|---|
| `__init__.py` | `__init__.py` | Keep |
| `__main__.py` | `__main__.py` | Keep |
| `constants.py` | `constants.py` | Keep |

### 3l. Tests (mirror production structure)

| Current path | New path | Action |
|---|---|---|
| `tests/cli/` | `tests/cli/` | Adjust imports |
| `tests/core/` | `tests/core/` | Adjust imports (path changes) |
| `tests/daemon/` | `tests/cli/daemon/` | Move |
| `tests/extractors/` | `tests/core/sources/` | Move |
| `tests/pipeline/` | `tests/core/pipeline/` | Move |
| `tests/ui/` | `tests/cli/tui/` | Move |
| `tests/utils/` | `tests/utils/` | Adjust imports |
| `tests/conftest.py` | `tests/conftest.py` | Update imports |
| `tests/plugin.py` | `tests/plugin.py` | Update imports |

---

## 4. New Structure in Detail

### 4a. `core/sources/` — The Branching Point

Each source handler implements:

```python
# core/sources/base.py
from dataclasses import dataclass
from typing import Protocol

@dataclass
class VideoInfo:
    url: str                     # Resolved YouTube URL
    title: str                   # Clean title (or raw for YouTube)
    artist: str | None
    album: str | None
    cover_url: str | None        # Pre-resolved cover URL (if available)
    source: str                  # "youtube", "youtubemusic", "spotify"
    raw_title: str | None        # Original title before cleaning

class SourceHandler(Protocol):
    """Handle one type of input URL → list of VideoInfo."""
    def handles(self, url: str) -> bool: ...
    def extract(self, url: str) -> list[VideoInfo]: ...
```

`core/sources/youtube.py` — handles youtube.com and music.youtube.com URLs. Uses yt-dlp to extract info. Returns list of VideoInfo (one per track, even for playlists/albums).

`core/sources/spotify.py` — handles open.spotify.com URLs. Calls Spotify API (via `core/clients/spotify/`), resolves each track to a YouTube search query, returns list of VideoInfo with resolved search terms.

### 4b. `core/pipeline/` — The Merged Pipeline

```python
# core/pipeline/context.py
@dataclass
class PipelineContext:
    video: VideoInfo
    audio_path: Path | None = None
    lyrics_path: Path | None = None
    cover_path: Path | None = None
    errors: list[Exception] = field(default_factory=list)
```

Each stage is a pure function or callable class:

```python
# core/pipeline/stages/download.py
class DownloadStage:
    def __init__(self, ytdlp_client, console, config):
        ...
    def __call__(self, ctx: PipelineContext) -> PipelineContext:
        ...
```

This makes each stage independently testable — inject mock clients, assert output context.

### 4c. `core/clients/` — External API Wrappers

Thin wrappers with:
- HTTP request logic (using `utils/network.py` session)
- Response parsing
- Typed return values
- Module-specific exceptions (if callers need to distinguish)

```python
# core/clients/music_brainz.py — ~80 lines, 1 file
# core/clients/webshare.py — ~50 lines, 1 file
```

### 4d. `core/lyrics/` — Lyrics Provider Infrastructure

Keeps the existing well-designed Strategy + Facade pattern from the current `lyrics/` module. The `engine.py` facade is the entry point for `core/pipeline/stages/lyrics.py`.

The `cleaner.py` (title cleaning) moves to `core/pipeline/cleaners/title.py` because it's a pipeline concern, not a client concern.

### 4e. `core/cover/` — Cover Provider Infrastructure

Moved from `services/cover/` since it's core business logic. Same Strategy pattern as lyrics. `core/pipeline/stages/cover.py` is the orchestrator that calls cover providers and passes results to the pipeline context.

### 4f. `core/domain/` — Pure Domain

Contains the "boring" but essential domain infrastructure:
- `models.py` — core data structures
- `config.py` — config load/save
- `cache.py` — file-based caching
- `env.py` — env detection
- `exceptions.py` — base TetodlError + domain exceptions

### 4g. `cli/` — Composition Root + Presentation

Everything under `cli/` is the UI layer:
- `parser.py` — argument parsing
- `dispatch.py` — command routing
- `commands/` — thin handlers that call core logic
- `daemon/` — HTTP server
- `tui/` — Textual-based TUI

The `cli/` layer is the only place where `console.err()` is allowed. All core code raises exceptions.

---

## 5. Dependency Rules

```
┌─────────────────────────────────────────────────────────────────┐
│                          constants.py                             │
│  (semua layer boleh import)                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                            utils/                                 │
│  ⛔ Zero imports from tetodl.*                                    │
│  ✅ Only stdlib + third-party                                     │
│  📁 console/, files.py, network.py, i18n.py, formatters.py, ...   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                            core/                                  │
│  ✅ May import from utils/ and constants.py                       │
│  ⛔ Must NOT import from cli/                                     │
│  📁 sources/, pipeline/, lyrics/, cover/, clients/, domain/,      │
│     dependency.py, maintenance.py, search.py, resolver.py,         │
│     extractor.py                                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                            cli/                                   │
│  ✅ May import from core/ and utils/                              │
│  ⛔ Must NOT import from cli/ → core/ (reverse)                   │
│  📁 commands/, daemon/, tui/, parser.py, dispatch.py, utils.py    │
└─────────────────────────────────────────────────────────────────┘
```

### Internal `core/` dependency rules

| Source | May import from |
|---|---|
| `core/domain/` | `utils/`, `constants` |
| `core/clients/` | `utils/`, `constants`, `core/domain/exceptions.py`, `core/domain/models.py` |
| `core/sources/` | `utils/`, `constants`, `core/domain/`, `core/clients/` |
| `core/pipeline/` | `utils/`, `constants`, `core/domain/`, `core/clients/`, `core/lyrics/`, `core/cover/`, `core/sources/` |
| `core/lyrics/` | `utils/`, `constants`, `core/domain/`, `core/clients/` |
| `core/cover/` | `utils/`, `constants`, `core/domain/`, `core/clients/` |

**No circular imports.** If `A` imports `B`, `B` must not import `A`. This is enforced by the directionality above.

---

## 6. SOLID & Design Patterns

### 6a. SOLID mapping

| Principle | How the 3-layer structure applies it |
|---|---|
| **Single Responsibility** | Every file has exactly one reason to change. `CoverService` changes when cover download logic changes. `SpotifyClient` changes when Spotify API changes. `PipelineContext` changes when data flow changes. |
| **Open/Closed** | New source (Deezer) → add `core/sources/deezer.py`. New lyrics provider → add `core/lyrics/providers/deezer.py`. No existing code modified. |
| **Liskov Substitution** | `SourceHandler` protocol → `YouTubeHandler` and `SpotifyHandler` are interchangeable. `LyricsProvider` → `LRCLIBProvider` and `GeniusProvider` are swappable. |
| **Interface Segregation** | `SourceHandler` has 2 methods (`handles`, `extract`). `LyricsProvider` has 1 method (`search`). No fat interfaces. Pipeline stages only know `PipelineContext`. |
| **Dependency Inversion** | Pipeline stages depend on abstractions (protocols/interfaces), not on concrete clients. `core/clients/` implements those abstractions. |

### 6b. Design patterns used

| Pattern | Where | Why |
|---|---|---|
| **Pipeline** | `core/pipeline/runner.py` + `stages/` | Sequential processing with shared context. Each stage is isolated, testable, and replaceable. |
| **Strategy** | `core/lyrics/providers/`, `core/cover/providers/`, `core/pipeline/cleaners/title.py` | Multiple algorithms for the same task, swappable at runtime. |
| **Facade** | `core/lyrics/engine.py`, `core/cover/image.py` | Hide complex provider orchestration behind a simple `search_lyrics()` / `fetch_cover()` API. |
| **Composite** | `core/pipeline/runner.py` | Pipeline is composed of stages; the runner itself can be treated as a stage. |
| **Factory** | Source detection: `sources/base.py` → URL pattern → instantiate correct handler | Decouples URL parsing from handler creation. |
| **Protocol (GoF Interface)** | `SourceHandler`, `LyricsProvider`, `CoverProvider`, `PipelineStage` | Python's structural typing (Protocol) for duck-typed polymorphism without inheritance. |

### 6c. Why these patterns specifically

| Requirement | Pattern solution |
|---|---|
| **Branching → merge** | Pipeline starts with source detection (Factory), branches into source-specific extraction (Strategy), then merges into common stages (Pipeline). |
| **YouTube title cleaning** | Strategy per source: `YouTubeCleaner` strips "Official Video", `NullCleaner` for Spotify/YT Music. Injected into `pipeline/stages/lyrics.py`. |
| **Cover URL source-specific** | Strategy: YouTube provides cover URL from yt-dlp (written to context), Spotify provides cover URL from API. Pipeline stage just downloads from URL. |
| **Add new source** | Implement `SourceHandler` + add to factory. No pipeline changes. |
| **Add new lyrics provider** | Implement `LyricsProvider` + add to engine. No caller changes. |
| **Test in isolation** | Every stage accepts dependencies. Mock clients, assert context changes. |

---

## 7. File Size Budget

Every file in the new structure is capped at **~300 lines maximum**. Files that exceed this are split into smaller modules. This prevents the "one huge file" problem the user worried about.

| File | Estimated size | Notes |
|---|---|---|
| `core/sources/youtube.py` | ~200 lines | URL parse + yt-dlp call + VideoInfo conversion |
| `core/sources/spotify.py` | ~150 lines | API call + search query generation |
| `core/pipeline/stages/download.py` | ~120 lines | yt-dlp download wrapper |
| `core/pipeline/stages/lyrics.py` | ~100 lines | Orchestrator: call engine, write to context |
| `core/pipeline/stages/cover.py` | ~100 lines | Orchestrator: download image from URL |
| `core/pipeline/stages/finalize.py` | ~150 lines | FFmpeg metadata embed + file rename |
| `core/pipeline/runner.py` | ~80 lines | Sequential stage execution |
| `core/pipeline/context.py` | ~60 lines | Dataclasses only |
| `core/pipeline/cleaners/title.py` | ~100 lines | Per-source title cleaning strategies |
| `core/lyrics/engine.py` | ~150 lines | Facade: LRCLIB + Genius orchestration |
| `core/lyrics/matcher.py` | ~120 lines | Scoring, fuzzy matching |
| `core/lyrics/providers/genius.py` | ~200 lines | Search + scrape + anchor alignment (most complex provider) |
| `core/lyrics/providers/lrclib.py` | ~100 lines | HTTP GET + multi-pass search |
| `core/lyrics/providers/itunes.py` | ~80 lines | HTTP GET + parse |
| `core/cover/image.py` | ~80 lines | Image download + cache |
| `core/cover/processor.py` | ~150 lines | Crop, convert, format |
| `core/cover/providers/deezer.py` | ~60 lines | Deezer API call |
| `core/clients/spotify/client.py` | ~200 lines | Main SpotifyClient class |
| `core/clients/spotify/auth.py` | ~80 lines | OAuth flow |
| `core/clients/spotify/models.py` | ~60 lines | Dataclasses |
| `core/clients/spotify/ratelimit.py` | ~50 lines | Rate limiter |
| `core/domain/config.py` | ~150 lines | Config load/save |
| `core/domain/cache.py` | ~100 lines | File-based caching |
| `core/domain/env.py` | ~200 lines | Environment detection |
| `core/domain/exceptions.py` | ~50 lines | Exception classes |
| `core/domain/tagger.py` | ~250 lines | FFmpeg metadata embedding (may split later) |
| All `utils/` files | 50–200 lines each | Pure helpers, no business logic |

**Hot take:** If any file exceeds 300 lines during development, the first question is "does it have multiple responsibilities?" — not "is this normal?" It is a deliberate signal to split.

---

## 8. Migration Phases

### Phase 0: Create `core/domain/` + `core/exceptions.py`

- Move `core/models.py`, `core/config.py`, `core/cache.py`, `core/history.py`, `core/tagger.py`, `core/registry.py`, `core/step.py` → `core/domain/`
- Move `core/env.py` → `core/domain/env.py`
- Create `core/domain/exceptions.py` with base `TetodlError`, `ConfigError`, `CacheError`, etc.
- Update all imports across the codebase
- **No behavior change** — pure directory move + import rewrite
- Tests: run full suite, fix import paths

### Phase 1: Move `services/cover/` → `core/cover/`

- Move all files from `services/cover/` to `core/cover/`
- Update imports in pipeline steps and other callers
- Delete `services/` after confirming empty
- Tests: run full suite, fix import paths

### Phase 2: Move `pipeline/` → `core/pipeline/`

- Move all files from `pipeline/` to `core/pipeline/`
- Rename `pipeline.py` → `runner.py` (to avoid name collision with package)
- Rename `steps/` → `stages/` (clearer name)
- Update ALL imports (`tetodl.pipeline.*` → `tetodl.core.pipeline.*`)
- Tests: run full suite

### Phase 3: Move `lyrics/` → `core/lyrics/`

- Move all files from `lyrics/` to `core/lyrics/`
- Move `lyrics/cleaner.py` → `core/pipeline/cleaners/title.py` (it's a pipeline concern)
- Update ALL imports
- Tests: run full suite

### Phase 4: Move `extractors/` → `core/sources/`

- Move all files from `extractors/` to `core/sources/`
- Rename `extractors/youtube.py` → `sources/youtube.py`, etc.
- Update ALL imports
- Tests: run full suite

### Phase 5: Merge `core/spotify/` → `core/clients/spotify/`

- Move all files from `core/spotify/` to `core/clients/spotify/`
- Update ALL imports (`tetodl.core.spotify.*` → `tetodl.core.clients.spotify.*`)
- Tests: run full suite

### Phase 6: Merge `ui/` → `cli/tui/` + `daemon/` → `cli/daemon/` + share/static

- Move `ui/*` (except `ui/entry/`) → `cli/tui/`
- Move `ui/entry/*` → `cli/tui/entry/`
- Move `daemon/*` → `cli/daemon/` including `daemon/static/` → `cli/daemon/static/`
- Move `utils/share.py` → `cli/share.py`
- Move `utils/share_static/` → `cli/static/`
- Extract `start_share_server` from `utils/network.py` → `cli/network.py`
- Merge `cli/parser.py` and `cli/dispatch.py` → add `cli/commands/`
- Update ALL imports (including `utils.share` → `cli.share`, `utils.network.start_share_server` → `cli.network`)
- Tests: run full suite

### Phase 7: Fix `utils/` layer violations (ongoing)

- `utils/display.py` — parameterize core imports instead of importing directly
- `utils/files.py` — check for core imports, remove if any
- All other `utils/` files must have zero `from tetodl.core.*` imports
- Create `utils/locales/` by moving `locales/`

### Execution order diagram

```
      ┌──────────────────────────────────────────────────────────────────────────┐
      │  Helper Consolidation (§12) — runs in parallel with any phase           │
      │  (text_cleaner, metadata, formatters, itunes cleanup)                   │
      └──────────────────────────────────────────────────────────────────────────┘

Phase 0 ──► Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5 ──► Phase 6 ──► Phase 7
(domain)   (cover)     (pipeline)  (lyrics)    (sources)   (spotify)   (ui merge)  (utils fix)

Each phase = 1 commit. Track progress in plan/REFACTOR_TRACKER.md.
```

Phases 0–6 are **pure directory moves + import rewrites** — no behavior changes. Phase 7 requires actual code changes (parameterization).

---

## 9. Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Missed import during move | Medium | High (runtime ImportError) | Run full test suite after each phase. `grep -r "old.path"` before/after. |
| Broken `cli/parser.py` imports | Low | High (app won't start) | Test `python3 -m tetodl --help` after each phase. |
| Circular import in `core/` | Low | High (Python deadlock) | Adhere to dependency direction in Section 5. Run `python3 -c "import tetodl"` after each phase. |
| `utils/` still has core imports | Medium | Low (violates rule but app works) | Phase 7 dedicated to fixing. CI check: `grep -r "from tetodl.core" tetodl/utils/` |
| Large file (300+ lines) | Medium | Low (still works, but signals needed split) | Enforce in code review. Split proactively. |
| Behavior change during move | Very Low | Critical | Moves are 100% mechanical. If behavior change is needed, do it in a separate commit. |

---

## 10. Verification Plan

```bash
# After each phase:
cd /path/to/tetodl

# 1. No import errors
python3 -c "import tetodl; print('OK')"

# 2. CLI starts
python3 -m tetodl --help

# 3. All tests pass
python3 -m pytest tetodl/tests/ -x --timeout=60

# 4. No stale imports from old paths
grep -r "from tetodl\.pipeline\." tetodl/ && echo "❌ FOUND" || echo "✅ OK"
grep -r "from tetodl\.extractors\." tetodl/ && echo "❌ FOUND" || echo "✅ OK"
grep -r "from tetodl\.lyrics\." tetodl/ && echo "❌ FOUND" || echo "✅ OK"
grep -r "from tetodl\.services\." tetodl/ && echo "❌ FOUND" || echo "✅ OK"
grep -r "from tetodl\.daemon\." tetodl/ && echo "❌ FOUND" || echo "✅ OK"
grep -r "from tetodl\.ui\." tetodl/ && echo "❌ FOUND" || echo "✅ OK"

# 5. utils/ is pure
grep -r "from tetodl\.\(core\|cli\|pipeline\|lyrics\|extractors\|services\|daemon\|ui\)" tetodl/utils/ && echo "❌ VIOLATION" || echo "✅ PURE"

# 6. core/ does not import cli/
grep -r "from tetodl\.cli" tetodl/core/ && echo "❌ VIOLATION" || echo "✅ OK"
```

---

## 11. Static Assets & Share Feature

### 11a. Current state

| Asset | Current location | Used by |
|---|---|---|
| Daemon web UI HTML | `daemon/static/index.html` | `daemon/api.py` (StaticFiles mount via `file_mode`) |
| Share feature CSS | `utils/share_static/styles.css` | `utils/share.py` (loaded at import), `daemon/api.py` (via `_player_css()`) |
| Share feature JS | `utils/share_static/player.js` | `utils/share.py` (loaded at import), `daemon/api.py` (via `_player_js()`) |

### 11b. Dependency chain

```
utils/share.py               ← generates HTML, loads static files at import
  │
  ├── utils/network.py       ← lazy import: from ..utils.share import create_share_router
  │     │
  │     └── cli/parser.py    ← from ..utils.network import start_share_server
  │     └── cli/dispatch.py  ← from tetodl.utils.network import start_share_server
  │
  └── daemon/api.py          ← from ..utils.share import create_share_router, list_entries, stream_file
        └── reads share_static/styles.css + share_static/player.js
```

**Problem:** `utils/share.py` is presentation logic (HTML generation), not a pure utility. `utils/network.py` also has a presentation dependency through its lazy import. Both violate the `utils/` purity rule.

### 11c. Target placement

| Current | New home | Rationale |
|---|---|---|
| `utils/share.py` | `cli/share.py` | HTML generation = presentation layer |
| `utils/share_static/styles.css` | `cli/static/styles.css` | Static asset, belongs with UI |
| `utils/share_static/player.js` | `cli/static/player.js` | Static asset, belongs with UI |
| `daemon/static/index.html` | `cli/daemon/static/index.html` | Moves with daemon to `cli/` |
| `start_share_server` (in `utils/network.py`) | `cli/network.py` | Server start = CLI operation |

### 11d. SVG icons handling

`utils/share.py` exports an `SVG` dict with HTML icon strings. This dict is also imported by `daemon/api.py`:

```python
from ..utils.share import SVG as _SHARE_SVG
```

After the move:
- `SVG` stays in `cli/share.py` (it's presentation-specific)
- `daemon/api.py` (→ `cli/daemon/api.py`) imports from `cli.share` — both in `cli/`, no violation

The `icon_for_ext()` function (planned in `utils/formatters.py`) is a different concern — it maps file extensions to icon names, not HTML SVGs.

### 11e. Implementation steps (part of Phase 6)

1. Create `cli/static/` directory
2. Move `utils/share_static/*` → `cli/static/`
3. Move `utils/share.py` → `cli/share.py`; update `_STATIC_DIR` path
4. Extract `start_share_server` from `utils/network.py` → `cli/network.py`
5. Create `cli/daemon/static/`; move `daemon/static/index.html`
6. Update imports in:
   - `cli/parser.py` → import from `cli.network` instead of `utils.network`
   - `cli/dispatch.py` → same
   - `cli/daemon/api.py` → import from `cli.share` instead of `utils.share`; fix static path
7. Verify `utils/` has zero imports of share/static modules

---

## 12. Redundant Helper Consolidation

> These are adopted from `plan/REFACTOR.md` Sections 4 and 6. They are **architecture-independent** — the same consolidation is needed regardless of 3-layer or 4-layer.

### 12a. Title/Text Cleaning (`utils/text_cleaner.py`)

**Current duplications:**

| Function | Copies in |
|---|---|
| `_clean_title(title, artist)` | `services/cover/providers/deezer.py` (now `core/cover/providers/deezer.py`), `lyrics/providers/itunes.py` (now `core/lyrics/providers/itunes.py`), `lyrics/providers/genius.py` (now `core/lyrics/providers/genius.py`) — **3 copies** |
| `_get_search_queries(artist, title)` | `lyrics/providers/genius.py` (method), `services/cover/providers/genius.py` (module-level) — **2 copies** |
| `_normalize(s)` / `_normalize_line(line)` | `lyrics/matcher.py` — **2 variants**, nearly identical |
| `_has_non_alphabet(text)` | `lyrics/matcher.py` — **1 copy** (but should move with other text utils) |

**Consolidation target:** Create `utils/text_cleaner.py` with:

| Function | Source (authoritative) | Description |
|---|---|---|
| `clean_title(title, artist)` | Deezer version (most complete — handles `"\u00d7"`, `"album version"`) | Strip noise from YouTube titles |
| `normalize_text(text)` | Merged from matcher `_normalize()` | Strip non-alphanum, lowercase |
| `normalize_line(line)` | Merged from matcher `_normalize_line()` | Same + `.strip()` |
| `has_non_alphabet(text)` | Moved from matcher `_has_non_alphabet()` | Detect CJK, Hangul, Cyrillic |

**Files to update (4):**

| File | Change |
|---|---|
| `core/cover/providers/deezer.py` | Remove `_clean_title`, import `clean_title` from `utils.text_cleaner` |
| `core/lyrics/providers/itunes.py` | Remove `_clean_title`, import `clean_title` from `utils.text_cleaner` |
| `core/lyrics/providers/genius.py` | Remove `_clean_title`, import `clean_title` from `utils.text_cleaner` |
| `core/cover/providers/genius.py` | Change import: `from tetodl.utils.text_cleaner import clean_title` (was import from `core.lyrics.providers.genius`) |

Also update `core/lyrics/matcher.py` to import `normalize_text` / `normalize_line` / `has_non_alphabet` from `utils.text_cleaner` instead of defining its own.

### 12b. Artist/Title Resolution (`utils/metadata.py`)

**Current duplications:**

| Function | File | Purpose |
|---|---|---|
| `_resolve_artist_title(info, ctx)` | `pipeline/steps/cover.py` (`core/pipeline/stages/cover.py` after Phase 2) | Resolve clean artist/title from yt-dlp info |
| `_resolve_search_terms(info, cover_result, ctx)` | `pipeline/steps/lyrics.py` (`core/pipeline/stages/lyrics.py` after Phase 2) | Same resolution + accepts cover_result |

Both implement the same priority chain and the same swap heuristic. The only difference: lyrics step accepts `cover_result` as additional metadata source.

**Consolidation target:** Create `utils/metadata.py` with:

```python
def resolve_artist_title(
    info: MediaInfo,
    ctx: PipelineContext | None = None,
    cover_result: CoverResult | None = None
) -> tuple[str, str]:
```

Priority chain (merged):
1. `ctx.spotify_title` / `ctx.spotify_artist` (if exists)
2. `cover_result.metadata` (lyrics step only)
3. `info.artist` / `info.track` (YT Music structured metadata)
4. `clean_youtube_title(info.title)` (iTunes API → regex fallback)
5. `info.uploader` / `info.title` (last resort, raw YouTube)

Swap heuristic: when `cleaned_title == uploader_clean` but `artist != uploader_clean`, swap them.

**Files to update (2):**

| File | Change |
|---|---|
| `core/pipeline/stages/cover.py` | Remove `_resolve_artist_title`, import from `utils.metadata` |
| `core/pipeline/stages/lyrics.py` | Remove `_resolve_search_terms`, import from `utils.metadata` |

### 12c. Formatting Consolidation (`utils/formatters.py`)

**Current duplications:**

| Function | Source 1 | Source 2 | Action |
|---|---|---|---|
| `_icon(ext)` | `daemon/api.py` | — | Move to `utils/formatters.py` |
| `_classify(ext)` | `utils/share.py` | — | Merge with `_icon` → single `icon_for_ext()` |
| `_size_str(size)` | `daemon/api.py` | — | Move to `utils/formatters.py` |
| `_human_size(size)` | `utils/share.py` | — | Merge → `human_size()` |

**Add to `utils/formatters.py`:**

```python
def human_size(size: int) -> str:
    """Bytes → human-readable (e.g., '12.5 MB')."""

def icon_for_ext(ext: str) -> str:
    """File extension → SVG icon or emoji."""
```

**Files to update (2):**

| File | Change |
|---|---|
| `cli/daemon/api.py` | Remove `_icon`, `_size_str`; import `icon_for_ext`, `human_size` from `utils.formatters` |
| `cli/share.py` | Remove `_classify`, `_human_size`; import `icon_for_ext`, `human_size` from `utils.formatters` |

### 12d. Remove Private `_is_valid_match`

| File | Change |
|---|---|
| `core/lyrics/providers/itunes.py` | Replace call to local `_is_valid_match()` with `is_valid_match()` imported from `core/lyrics/matcher.py` |

---

## 13. Import Tracking & Git Workflow

### 13a. Tracking document

A separate living document `plan/REFACTOR_TRACKER.md` tracks every file, every import change, and every phase's completion status. It contains:

- **Import Change Tracker (§1)** — per-file table of old paths, new paths, and all import paths that need rewriting. Grouped by phase.
- **Duplicate Helper Consolidation Tracker (§2)** — same for the helper dedup work.
- **Phase Checklist (§3)** — checkboxes for every atomic move/edit in each phase.
- **Verification Commands (§4)** — copy-paste commands to verify each phase.

Run `git diff` against the tracker before/after each phase to confirm intent matches reality.

### 13b. Git workflow

```
main (production)
 │
 ├── refactor/restructure (this branch)
 │     ├── Phase 0 commit
 │     ├── Phase 1 commit
 │     ├── Phase 2 commit
 │     ├── ... (one commit per phase)
 │     └── Phase 7 commit
 │
 └── (future: PR refactor/restructure → main)
```

| Step | Command |
|---|---|
| Start | `git checkout -b refactor/restructure main` |
| After each phase | `git add -A && git commit -m "phase-N: description"` |
| Push | `git push origin refactor/restructure` |
| Verify diff | `git diff --stat HEAD~1 HEAD` (should match expected files for that phase) |
| PR back to main | `gh pr create --base main --head refactor/restructure --title "Refactor: 3-layer architecture"` |

### 13c. Branch naming convention

Per repo convention (conventional commits + short names):
- `refactor/restructure` — this work
- Previously: `main`, `dev`

All future refactoring work follows: `refactor/<short-description>`.

### 13d. Commit message convention

Following the existing pattern (`type(scope): description`):

| Phase | Example commit message |
|---|---|
| 0 | `refactor(domain): move core models/config/cache to core/domain/` |
| 1 | `refactor(cover): move services/cover/ to core/cover/` |
| 2 | `refactor(pipeline): move pipeline/ to core/pipeline/ with rename steps→stages` |
| 3 | `refactor(lyrics): move lyrics/ to core/lyrics/, cleaner to pipeline/cleaners/` |
| 4 | `refactor(sources): move extractors/ to core/sources/ as SourceHandler` |
| 5 | `refactor(spotify): move core/spotify/ to core/clients/spotify/` |
| 6 | `refactor(ui): merge daemon/ + ui/ + share into cli/` |
| 7 | `refactor(utils): fix all layer violations, move locales, enforce purity` |
| Helpers | `refactor(helpers): consolidate duplicate title/metadata/formatter utilities` |

| Concern | 4-layer answer | 3-layer answer |
|---|---|---|
| "Where does this file go?" | "Depends if it's 'core' or 'services' — you figure it out" | **One rule: if it's business logic, it's in `core/`** |
| "Why is Spotify in core but YouTube extractor in services?" | "Uh... Spotify is more 'core'?" | **Both in `core/` — Spotify is `core/clients/spotify/`, YouTube is `core/sources/youtube/`** |
| "How do I add a new pipeline stage?" | "Add to `core/pipeline/steps/`, import from `services/`" | **Add to `core/pipeline/stages/`, import from `core/clients/`** |
| "How do I prevent file size blowup?" | No explicit limit | **~300 line soft cap per file** |
| "How do I prevent utils violations?" | Phase 4 (partial fix) | **Phase 7 (complete fix) + CI enforcement** |
| "What are the top-level dirs?" | 4 (`core`, `services`, `utils`, `ui`) | **3 (`cli`, `core`, `utils`)** — simpler mental model |
