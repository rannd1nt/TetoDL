import pytest


class TestPipelineStep:
    """Tests for PipelineStep ABC."""

    def test_pipeline_step_subclass_contract(self):
        """Subclasses that do not implement __call__ cannot be instantiated."""
        from tetodl.core.step import PipelineStep

        class IncompleteStep(PipelineStep[str, str]):
            pass

        with pytest.raises(TypeError):
            IncompleteStep()  # type: ignore[abstract]

    def test_pipeline_step_proper_subclass(self):
        """A subclass that implements __call__ can be instantiated and invoked."""
        from tetodl.core.step import PipelineStep

        class UpperStep(PipelineStep[str, str]):
            def __call__(self, data: str) -> str:
                return data.upper()

        step = UpperStep()
        assert step("hello") == "HELLO"

    def test_pipeline_step_generic_types(self):
        """PipelineStep works with numeric types."""
        from tetodl.core.step import PipelineStep

        class DoubleStep(PipelineStep[int, int]):
            def __call__(self, data: int) -> int:
                return data * 2

        step = DoubleStep()
        assert step(21) == 42


class TestPipelineError:
    """Tests for PipelineError exception."""

    def test_pipeline_error_attributes(self):
        """PipelineError stores message, step_name, and recoverable."""
        from tetodl.core.step import PipelineError
        err = PipelineError("something failed", step_name="extract", recoverable=True)
        assert err.step_name == "extract"
        assert err.recoverable is True
        assert "something failed" in str(err)
        assert "[extract]" in str(err)

    def test_pipeline_error_defaults(self):
        """PipelineError defaults step_name to '' and recoverable to False."""
        from tetodl.core.step import PipelineError
        err = PipelineError("generic error")
        assert err.step_name == ""
        assert err.recoverable is False

    def test_pipeline_error_caught(self):
        """PipelineError can be raised and caught."""
        from tetodl.core.step import PipelineError

        def failing_step():
            raise PipelineError("fail", step_name="test", recoverable=False)

        with pytest.raises(PipelineError) as exc_info:
            failing_step()
        assert exc_info.value.step_name == "test"
        assert exc_info.value.recoverable is False
