# Copyright 2026 rannd1nt
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from unittest.mock import MagicMock, patch

from tetodl.core.domain.models import MediaInfo, PipelineContext
from tetodl.core.domain.step import PipelineError
from tetodl.core.pipeline.stages.extract import ExtractStep


class TestExtractStep:
    """Tests for ExtractStep."""

    def test_extract_step_requires_media_info(self, pipeline_ctx: PipelineContext):
        """Returns ctx unchanged when resolve_extractor raises PipelineError."""
        step = ExtractStep()

        with patch(
            "tetodl.core.pipeline.stages.extract.resolve_extractor",
            side_effect=PipelineError("no extractor", "extract"),
        ):
            result = step(pipeline_ctx)

        assert result.error is not None
        assert "no extractor" in result.error

    def test_extract_step_success(self, pipeline_ctx: PipelineContext):
        """Populates media_info when extraction succeeds."""
        step = ExtractStep()
        fake_media = MediaInfo(
            id="abc123",
            title="Test Song",
            url="https://youtube.com/watch?v=abc123",
            duration=240,
            uploader="Test Artist",
        )
        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = fake_media

        with patch(
            "tetodl.core.pipeline.stages.extract.resolve_extractor",
            return_value=mock_extractor,
        ):
            result = step(pipeline_ctx)

        assert result.media_info is not None
        assert result.media_info.id == "abc123"
        assert result.media_info.title == "Test Song"
        assert result.error is None

    def test_extract_step_extract_failure(self, pipeline_ctx: PipelineContext):
        """Sets ctx.error when the extractor raises PipelineError."""
        step = ExtractStep()
        mock_extractor = MagicMock()
        mock_extractor.extract.side_effect = PipelineError(
            "extraction failed",
            "extract",
        )

        with patch(
            "tetodl.core.pipeline.stages.extract.resolve_extractor",
            return_value=mock_extractor,
        ):
            result = step(pipeline_ctx)

        assert result.error is not None
        assert "extraction failed" in result.error
        assert result.media_info is None
