#!/usr/bin/env bash
# ===========================================================================
# test-linux.sh — Comprehensive binary test suite for TetoDL on Linux
# Produces JUnit XML for GitHub Actions integration.
#
# Usage:
#   ./test-linux.sh --binary ./dist/tetodl-linux [--test-url URL] [--playlist-url URL] [--timeout SEC] [--ytdlp-update]
#
# Parameters:
#   --binary       Path to the tetodl binary (required)
#   --test-url     Single-video YouTube URL (default: https://youtu.be/jQhArAdrAtU)
#   --playlist-url Playlist YouTube URL (default: https://youtube.com/playlist?list=PLCmop9hr8TtM)
#   --timeout      Per-test timeout in seconds (default: 120)
#   --ytdlp-update Also run yt-dlp update check tests (requires network)
# ===========================================================================
set -euo pipefail

# ---- Parse args ----
BINARY=""
TEST_URL="https://youtu.be/jQhArAdrAtU"
PLAYLIST_URL="https://youtube.com/playlist?list=PLCmop9hr8TtM"
TIMEOUT=120
YTDLP_UPDATE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --binary) BINARY="$2"; shift 2 ;;
        --test-url) TEST_URL="$2"; shift 2 ;;
        --playlist-url) PLAYLIST_URL="$2"; shift 2 ;;
        --timeout) TIMEOUT="$2"; shift 2 ;;
        --ytdlp-update) YTDLP_UPDATE=true; shift ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

if [[ -z "$BINARY" ]]; then
    echo "ERROR: --binary is required"
    exit 1
fi
if [[ ! -x "$BINARY" ]]; then
    echo "ERROR: binary not found or not executable: $BINARY"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT_DIR="$ROOT_DIR/test-results"
mkdir -p "$OUT_DIR"

PASSED=()
FAILED=()
START_TIME=$(date +%s)

# ---- Helpers ----
_RUN_EC=0
run_test() {
    local name="$1" args="$2" timeout="${3:-$TIMEOUT}"
    echo ""
    echo "=== $name ==="

    local out_file="$OUT_DIR/${name}.out"
    local err_file="$OUT_DIR/${name}.err"

    set +e
    timeout "$timeout" "$BINARY" $args >"$out_file" 2>"$err_file"
    _RUN_EC=$?
    set -e

    if [[ $_RUN_EC -eq 124 ]]; then
        echo "  TIMEOUT after ${timeout}s"
        return 0
    fi

    local output
    output="$(cat "$out_file" 2>/dev/null || true)$(cat "$err_file" 2>/dev/null || true)"
    printf "%s" "$output"
}

run_test_blocking() {
    local name="$1" args="$2" wait_sec="${3:-5}"
    echo ""
    echo "=== $name ==="

    set +e
    "$BINARY" $args &
    local pid=$!
    set -e

    sleep "$wait_sec"

    if ! kill -0 "$pid" 2>/dev/null; then
        wait "$pid" 2>/dev/null || true
        echo "  Process exited prematurely"
        FAILED+=("$name")
        return 1
    fi

    kill "$pid" 2>/dev/null || true
    sleep 1
    kill -9 "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    PASSED+=("$name")
    echo "  PASS"
    return 0
}

assert_match() {
    local output="$1" pattern="$2"
    if ! echo "$output" | grep -qE "$pattern"; then
        echo "  FAIL: Expected pattern not found: $pattern"
        return 1
    fi
    return 0
}

assert_not_match() {
    local output="$1" pattern="$2"
    if echo "$output" | grep -qE "$pattern"; then
        echo "  FAIL: Unexpected pattern found: $pattern"
        return 1
    fi
    return 0
}

assert_exit_code() {
    local actual="$1" expected="${2:-0}"
    if [[ "$actual" -ne "$expected" ]]; then
        echo "  FAIL: Expected exit code $expected, got $actual"
        return 1
    fi
    return 0
}

record_test() {
    local name="$1" result="$2"
    if [[ "$result" -eq 0 ]]; then
        PASSED+=("$name")
        echo "  PASS"
    else
        FAILED+=("$name")
    fi
}

# ---- Helper: run a test and assert ----
execute_and_assert() {
    local name="$1" args="$2"
    shift 2

    local capture_file="$OUT_DIR/${name}.capture"
    _RUN_EC=0
    run_test "$name" "$args" "$TIMEOUT" > "$capture_file" 2>/dev/null || true
    local result
    result="$(cat "$capture_file" 2>/dev/null || true)"

    local expected_ec=0
    local match_pattern=""
    local not_match_pattern=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --exit) expected_ec="$2"; shift 2 ;;
            --match) match_pattern="$2"; shift 2 ;;
            --not-match) not_match_pattern="$2"; shift 2 ;;
            *) echo "Unknown assert: $1"; exit 1 ;;
        esac
    done

    local ec="${_RUN_EC:-1}"
    local ok=0
    assert_exit_code "$ec" "$expected_ec" || ok=1

    if [[ -n "$match_pattern" ]]; then
        assert_match "$result" "$match_pattern" || ok=1
    fi
    if [[ -n "$not_match_pattern" ]]; then
        assert_not_match "$result" "$not_match_pattern" || ok=1
    fi

    record_test "$name" "$ok"
}

# ===========================================================================
# PHASE 1: Command-Line Parsing
# ===========================================================================
echo ""
echo "========================================"
echo "  PHASE 1: Command-Line Parsing"
echo "========================================"

execute_and_assert "help" "--help" --exit 0 --match "usage"
execute_and_assert "version" "--version" --exit 0 --match "[0-9]+\.[0-9]+\.[0-9]+"
execute_and_assert "info" "--info" --exit 0 --match "TetoDL"
execute_and_assert "invalid-flag" "--bogus-flag" --exit 2 --match "unrecognized"
execute_and_assert "recheck" "--recheck" --exit 0 --match "dependency|check|ffmpeg|yt-dlp"

# ===========================================================================
# PHASE 2: Video Downloads
# ===========================================================================
echo ""
echo "========================================"
echo "  PHASE 2: Video Downloads"
echo "========================================"

execute_and_assert "video-basic" "-v \"$TEST_URL\"" --exit 0 --not-match "ffmpeg is not installed|ERROR"
execute_and_assert "video-resolution" "-v -r 720p \"$TEST_URL\"" --exit 0 --not-match "ffmpeg is not installed"

# ===========================================================================
# PHASE 3: Audio Downloads (core features)
# ===========================================================================
echo ""
echo "========================================"
echo "  PHASE 3: Audio Downloads"
echo "========================================"

execute_and_assert "audio-basic" "-a \"$TEST_URL\"" --exit 0 --not-match "ERROR|ffmpeg is not installed"
execute_and_assert "audio-format-mp3" "-a -f mp3 \"$TEST_URL\"" --exit 0 --not-match "ERROR"
execute_and_assert "audio-format-m4a" "-a -f m4a \"$TEST_URL\"" --exit 0
execute_and_assert "audio-smart-cover" "-a --smart-cover \"$TEST_URL\"" --exit 0 --match "cover|Cover|iTunes|thumb"
execute_and_assert "audio-no-cover" "-a --no-cover \"$TEST_URL\"" --exit 0 --not-match "Processing cover|Embedding cover"
execute_and_assert "audio-lyrics" "-a --lyrics \"$TEST_URL\"" --exit 0 --match "lyrics|Lyrics|Genius"
execute_and_assert "audio-cut" "-a --cut 0:10-0:20 \"$TEST_URL\"" --exit 0 --not-match "ffmpeg is not installed"
execute_and_assert "audio-quiet" "-a --quiet \"$TEST_URL\"" --exit 0
execute_and_assert "audio-output-path" "-a -o \"$OUT_DIR/custom_output\" \"$TEST_URL\"" --exit 0
execute_and_assert "audio-combo" "-a --smart-cover --lyrics -f m4a \"$TEST_URL\"" --exit 0 --not-match "ERROR"

# ===========================================================================
# PHASE 4: Thumbnail
# ===========================================================================
echo ""
echo "========================================"
echo "  PHASE 4: Thumbnail"
echo "========================================"

execute_and_assert "thumbnail-only" "--thumbnail-only \"$TEST_URL\"" --exit 0
execute_and_assert "thumbnail-format-png" "--thumbnail-only -f png \"$TEST_URL\"" --exit 0

# ===========================================================================
# PHASE 5: Playlists
# ===========================================================================
echo ""
echo "========================================"
echo "  PHASE 5: Playlists"
echo "========================================"

execute_and_assert "playlist-basic" "-a \"$PLAYLIST_URL\"" --exit 0 --not-match "ERROR"
execute_and_assert "playlist-items" "-a --items 1 \"$PLAYLIST_URL\"" --exit 0 --not-match "ERROR"
execute_and_assert "playlist-async" "-a --async \"$PLAYLIST_URL\"" --exit 0 --not-match "ERROR"
execute_and_assert "playlist-async-items" "-a --async --items 1 \"$PLAYLIST_URL\"" --exit 0 --not-match "ERROR"
execute_and_assert "playlist-group" "-a --group TestGroup \"$PLAYLIST_URL\"" --exit 0 --match "group|Group|TestGroup"
execute_and_assert "playlist-m3u" "-a --m3u \"$PLAYLIST_URL\"" --exit 0 --not-match "ERROR"
execute_and_assert "playlist-async-group-m3u" "-a --async --group TestFull --m3u \"$PLAYLIST_URL\"" --exit 0 --not-match "ERROR"

# ===========================================================================
# PHASE 6: Daemon
# ===========================================================================
echo ""
echo "========================================"
echo "  PHASE 6: Daemon"
echo "========================================"

run_test_blocking "daemon-run" "daemon -r" 8 || true

# ===========================================================================
# PHASE 7: yt-dlp Update Check (optional)
# ===========================================================================
if [[ "$YTDLP_UPDATE" == "true" ]]; then
    echo ""
    echo "========================================"
    echo "  PHASE 7: yt-dlp Update Check"
    echo "========================================"

    execute_and_assert "ytdlp-update-check" "--recheck" --exit 0 --match "yt-dlp|version|update"
    execute_and_assert "ytdlp-version-info" "--version" --exit 0 --match "[0-9]+\.[0-9]+\.[0-9]+"
fi

# ===========================================================================
# PHASE 8: Utility Commands
# ===========================================================================
echo ""
echo "========================================"
echo "  PHASE 8: Utility Commands"
echo "========================================"

execute_and_assert "history" "--history" --exit 0
execute_and_assert "uninstall-cancel" "--uninstall" --exit 0 --not-match "Traceback|unhandled exception"

# ===========================================================================
# Generate JUnit XML
# ===========================================================================
END_TIME=$(date +%s)
TOTAL=$(( ${#PASSED[@]} + ${#FAILED[@]} ))
DURATION=$(( END_TIME - START_TIME ))

XML_FILE="$ROOT_DIR/test-results.xml"
{
    echo '<?xml version="1.0"?>'
    echo "<testsuite name=\"tetodl.linux\" tests=\"$TOTAL\" failures=\"${#FAILED[@]}\" time=\"$DURATION\">"
    for name in "${PASSED[@]}"; do
        echo "  <testcase name=\"$name\" classname=\"tetodl.linux\" time=\"0\" />"
    done
    for name in "${FAILED[@]}"; do
        echo "  <testcase name=\"$name\" classname=\"tetodl.linux\" time=\"0\">"
        echo '    <failure message="Test failed" type="AssertionError"/>'
        echo "  </testcase>"
    done
    echo "</testsuite>"
} > "$XML_FILE"

echo ""
echo "========================================"
echo "  RESULTS: ${#PASSED[@]}/$TOTAL passed, ${#FAILED[@]} failed"
echo "  Report: $XML_FILE"
echo "========================================"

if [[ ${#FAILED[@]} -gt 0 ]]; then
    exit 1
fi
