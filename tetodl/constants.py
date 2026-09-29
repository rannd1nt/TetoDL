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

"""
Constants and Path Configuration
"""

APP_NAME = "TetoDL"
APP_VERSION = "2.3.4"
JITTER = (3.0, 5.0)

# ==== DOWNLOAD SETTINGS ====
DOWNLOAD_DELAY = 2
MAX_RETRIES = 3
RETRY_DELAY = 2

# ==== OTHER CONFIGURATION ====
VALID_RESOLUTIONS = ["4320p", "2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"]
VALID_CONTAINERS = ["mp4", "mkv"]
VALID_THUMBNAIL_FORMATS = ["jpg", "png", "webp"]
VALID_CODECS = ["default", "h264", "h265"]
HISTORY_DISPLAY_LIMIT = 20

# ==== AUDIO QUALITY OPTIONS ====
AUDIO_QUALITY_OPTIONS = {
    "mp3": {"ext": "mp3", "bitrate": "~192 kbps", "codec": "MP3 (Lossy)"},
    "m4a": {"ext": "m4a", "bitrate": "~128 kbps", "codec": "AAC (M4A)"},
    "opus": {"ext": "opus", "bitrate": "~160-180 kbps", "codec": "Opus (Best Quality)"},
}