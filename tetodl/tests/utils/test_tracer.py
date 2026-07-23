"""Tests for tetodl.utils.tracer."""

import json

import pytest

from tetodl.utils.logger import is_debug, set_debug
from tetodl.utils.tracer import (
    TraceEntry,
    TraceStore,
    get_trace_store,
    set_dump_path,
    trace,
    traced,
)


@pytest.fixture(autouse=True)
def reset_debug():
    was_debug = is_debug()
    yield
    set_debug(was_debug if was_debug else False)


@pytest.fixture
def store():
    return TraceStore()


class TestTraceEntry:
    def test_default_fields(self):
        entry = TraceEntry(
            kind="CALL", timestamp=1.0, thread_id=1,
            module="mod", name="fn", depth=0,
        )
        assert entry.kind == "CALL"
        assert entry.args is None
        assert entry.result is None
        assert entry.duration is None
        assert entry.context_msg is None

    def test_optional_fields(self):
        entry = TraceEntry(
            kind="RETURN", timestamp=2.0, thread_id=1,
            module="mod", name="fn", depth=0,
            result="42", duration=0.5,
        )
        assert entry.result == "42"
        assert entry.duration == 0.5


class TestTraceStore:
    def test_record_and_entries(self, store):
        entry = TraceEntry(
            kind="CALL", timestamp=1.0, thread_id=1,
            module="mod", name="fn", depth=0,
        )
        store.record(entry)
        assert len(store.entries) == 1
        assert store.entries[0].kind == "CALL"

    def test_clear(self, store):
        store.record(TraceEntry(
            kind="CALL", timestamp=1.0, thread_id=1,
            module="mod", name="fn", depth=0,
        ))
        store.clear()
        assert len(store.entries) == 0

    def test_last_returns_most_recent(self, store):
        for i in range(5):
            store.record(TraceEntry(
                kind="CALL", timestamp=float(i), thread_id=1,
                module="mod", name="fn", depth=0,
            ))
        last = store.last(2)
        assert len(last) == 2
        assert last[0].timestamp == 3.0
        assert last[1].timestamp == 4.0

    def test_last_default_n(self, store):
        for i in range(5):
            store.record(TraceEntry(
                kind="CALL", timestamp=float(i), thread_id=1,
                module="mod", name="fn", depth=0,
            ))
        assert len(store.last()) == 5

    def test_filter_by_kind(self, store):
        store.record(TraceEntry(
            kind="CALL", timestamp=0.0, thread_id=1,
            module="mod", name="fn", depth=0,
        ))
        store.record(TraceEntry(
            kind="RETURN", timestamp=1.0, thread_id=1,
            module="mod", name="fn", depth=0,
        ))
        calls = store.filter(kind="CALL")
        assert len(calls) == 1
        assert calls[0].kind == "CALL"

    def test_filter_by_module(self, store):
        store.record(TraceEntry(
            kind="CALL", timestamp=0.0, thread_id=1,
            module="utils.fetcher", name="fetch", depth=0,
        ))
        store.record(TraceEntry(
            kind="CALL", timestamp=1.0, thread_id=1,
            module="utils.parser", name="parse", depth=0,
        ))
        result = store.filter(module="utils")
        assert len(result) == 2

    def test_filter_by_module_exact(self, store):
        store.record(TraceEntry(
            kind="CALL", timestamp=0.0, thread_id=1,
            module="utils.fetcher", name="fetch", depth=0,
        ))
        result = store.filter(module="utils.fetcher")
        assert len(result) == 1

    def test_filter_empty_when_no_match(self, store):
        store.record(TraceEntry(
            kind="CALL", timestamp=0.0, thread_id=1,
            module="mod", name="fn", depth=0,
        ))
        assert len(store.filter(kind="RETURN")) == 0

    def test_filter_no_criteria_returns_all(self, store):
        for i in range(3):
            store.record(TraceEntry(
                kind="CALL", timestamp=float(i), thread_id=1,
                module="mod", name="fn", depth=0,
            ))
        assert len(store.filter()) == 3

    def test_depth_tracking(self, store):
        assert store.depth == 0
        store.push_depth()
        assert store.depth == 1
        store.push_depth()
        assert store.depth == 2
        store.pop_depth()
        assert store.depth == 1

    def test_pop_depth_clamped_at_zero(self, store):
        store.pop_depth()
        assert store.depth == 0

    def test_dump_writes_to_file(self, store, tmp_path):
        store.record(TraceEntry(
            kind="CALL", timestamp=1.0, thread_id=1,
            module="mod", name="fn", depth=0, args={"x": "1"},
        ))
        path = tmp_path / "trace.log"
        store.dump(path)
        assert path.exists()
        content = path.read_text()
        assert "CALL" in content
        assert "fn" in content

    def test_dump_json_writes_to_file(self, store, tmp_path):
        store.record(TraceEntry(
            kind="CALL", timestamp=1.0, thread_id=1,
            module="mod", name="fn", depth=0,
        ))
        path = tmp_path / "trace.json"
        store.dump_json(path)
        assert path.exists()
        data = json.loads(path.read_text())
        assert len(data) == 1
        assert data[0]["kind"] == "CALL"

    def test_dump_creates_parent_dirs(self, store, tmp_path):
        path = tmp_path / "nested" / "dir" / "trace.log"
        store.dump(path)
        assert path.exists()

    def test_auto_prune(self, store):
        for i in range(5001):
            store.record(TraceEntry(
                kind="CALL", timestamp=float(i), thread_id=1,
                module="mod", name="fn", depth=0,
            ))
        assert len(store.entries) == 5000

    def test_entries_returns_copy(self, store):
        entry = TraceEntry(
            kind="CALL", timestamp=0.0, thread_id=1,
            module="mod", name="fn", depth=0,
        )
        store.record(entry)
        entries_snapshot = store.entries
        store.clear()
        assert len(entries_snapshot) == 1


class TestTraceDecorator:
    def test_records_call_entry(self):
        set_debug(True)

        @trace
        def my_func(x: int) -> int:
            return x * 2

        my_func(21)
        store = get_trace_store()
        assert store is not None
        calls = store.filter(kind="CALL")
        assert len(calls) >= 1
        assert any("my_func" in e.name for e in calls)

    def test_records_return_entry(self):
        set_debug(True)

        @trace
        def add(a: int, b: int) -> int:
            return a + b

        add(1, 2)
        store = get_trace_store()
        assert store is not None
        returns = store.filter(kind="RETURN")
        assert len(returns) >= 1

    def test_records_exception_entry(self):
        set_debug(True)

        @trace
        def crash() -> None:
            raise ValueError("boom")

        with pytest.raises(ValueError):
            crash()

        store = get_trace_store()
        assert store is not None
        excs = store.filter(kind="EXCEPTION")
        assert len(excs) >= 1
        assert excs[-1].exception is not None
        assert "boom" in excs[-1].exception


class TestTracedContextManager:
    def test_records_context_entry(self):
        set_debug(True)

        with traced("hello context"):
            pass

        store = get_trace_store()
        assert store is not None
        contexts = store.filter(kind="CONTEXT")
        assert len(contexts) >= 1
        assert contexts[-1].context_msg == "hello context"


class TestGetTraceStore:
    def test_get_trace_store_returns_singleton_after_trace(self):
        set_debug(True)
        get_trace_store()

        @trace
        def f():
            pass

        f()

        store_after = get_trace_store()
        assert store_after is not None


class TestSetDumpPath:
    def test_set_dump_path_configures_store(self, tmp_path):
        set_debug(True)
        path = tmp_path / "auto_dump.log"
        set_dump_path(path)

        @trace
        def f():
            pass

        f()
        store = get_trace_store()
        assert store is not None
        assert store._dump_path == path
