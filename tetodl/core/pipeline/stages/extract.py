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

import tetodl.core.sources  # noqa: F401 — auto-registers extractors
from tetodl.core.domain.models import PipelineContext
from tetodl.core.domain.step import PipelineError, PipelineStep
from tetodl.core.extractor import resolve_extractor
from tetodl.utils.tracer import trace, traced


class ExtractStep(PipelineStep[PipelineContext, PipelineContext]):
    @trace
    def __call__(self, ctx: PipelineContext) -> PipelineContext:
        try:
            extractor = resolve_extractor(ctx.url)
        except PipelineError as exc:
            ctx.error = str(exc)
            return ctx

        try:
            ctx.media_info = extractor.extract(ctx.url)
        except PipelineError as exc:
            with traced(f'extract failed — {exc}'):
                ctx.error = str(exc)

        return ctx
