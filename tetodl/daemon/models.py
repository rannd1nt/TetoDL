
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
    smart_cover: bool = False
    no_cover: bool = False
    force_crop: bool = False
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
                "smart_cover": True,
                "lyrics": True
            }
        }

class PreviewRequest(BaseModel):
    url: str = Field(..., description="Media URL to preview")
