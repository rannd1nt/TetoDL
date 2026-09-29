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

import os

from tetodl.core.domain.models import PipelineContext
from tetodl.core.domain.step import PipelineStep
from tetodl.core.domain.tagger import embed_lyrics
from tetodl.core.lyrics import search_lyrics
from tetodl.core.pipeline.metadata import resolve_artist_title
from tetodl.utils.console import console
from tetodl.utils.i18n_keys import Keys
from tetodl.utils.tracer import trace, traced


class LyricsStep(PipelineStep[PipelineContext, PipelineContext]):
    @trace
    def __call__(self, ctx: PipelineContext) -> PipelineContext:
        if not (ctx.lyrics_mode or ctx.config.lyrics_mode) or ctx.media_type != "audio":
            return ctx

        if ctx.downloaded_file is None:
            return ctx

        audio_path = ctx.downloaded_file.path
        if not audio_path or not os.path.exists(audio_path):
            return ctx

        info = ctx.media_info
        if info is None:
            return ctx

        artist, title = resolve_artist_title(info, ctx=ctx, cover_result=ctx.cover_result)

        console.proc(Keys.media.searching_lyrics_for(artist=artist, title=title))
        duration = info.duration if info.duration else 0.0
        with traced('fetching lyrics via engine'):
            lyrics = search_lyrics(artist, title, duration=duration)

        if not lyrics:
            with traced('no lyrics returned'):
                console.warn(Keys.media.lyrics_not_found_genius)
                return ctx

        if embed_lyrics(audio_path, lyrics):
            with traced('embed successful'):
                console.ok(Keys.media.lyrics_embedded_success)
                ctx.lyrics_embedded = True
                return ctx

        with traced('embed failed'):
            console.err(Keys.media.failed_to_embed_lyrics)
            return ctx


