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

from pydantic import BaseModel, Field


class DownloadRequest(BaseModel):
    url: str | None = Field(None, description="Media URL to download")
    search_query: str | None = Field(None, description="Search YouTube interactively")
    search_limit: int = Field(5, description="Search limit")
    title: str | None = Field(None, description="Display title for the task (shown in UI)")

    audio_only: bool = False
    video_only: bool = False
    thumbnail_only: bool = False
    format: str | None = Field(None, description="Force format (mp3/m4a/opus | mp4/mkv | jpg/png)")
    resolution: str | None = Field(None, description="Max video resolution limit")
    codec: str | None = Field(None, description="Set video codec priority (default, h264, h265)")
    async_mode: bool = False

    cut_time: str | None = Field(None, description="Trim media (e.g. '01:30-02:00')")
    items: str | None = Field(None, description="Playlist items")
    group: str | bool | None = Field(None, description="Group downloads into a subfolder")
    m3u: bool = False
    zip: bool = False
    cover: bool = False
    metadata: bool = False
    no_enrich: bool = False
    lyrics: bool = False
    romaji: bool = False

    share: bool = False
    share_temp: bool = False
    spotify: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://youtu.be/...",
                "audio_only": True,
                "cover": True,
                "metadata": True,
                "lyrics": True
            }
        }

class PreviewRequest(BaseModel):
    url: str = Field(..., description="Media URL to preview")