# core/registry.py
import json
import os

from tetodl.utils.tracer import trace

from ..constants import REGISTRY_PATH


class RegistryManager:
    def __init__(self):
        self.data: dict[str, dict] = {"youtube": {}, "spotify": {}}
        self.load()

    def load(self):
        if os.path.exists(REGISTRY_PATH):
            try:
                with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                if "youtube" not in raw:
                    self.data = {"youtube": raw, "spotify": {}}
                else:
                    self.data = raw
            except Exception:
                self.data = {"youtube": {}, "spotify": {}}

    def save(self):
        try:
            with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, separators=(',', ':'))
        except Exception:
            pass

    def register_download(self, video_id, file_path, content_type, metadata, spotify_id=None):
        if not video_id or not content_type:
            return

        c_type = 'audio' if 'audio' in content_type.lower() or 'music' in content_type.lower() else 'video'
        abs_path = os.path.abspath(file_path)
        youtube = self.data.setdefault("youtube", {})
        spotify_index = self.data.setdefault("spotify", {})

        if video_id not in youtube:
            youtube[video_id] = {}

        if c_type not in youtube[video_id]:
            youtube[video_id][c_type] = {
                'paths': [],
                't': metadata.get('title', 'Unknown'),
                'a': metadata.get('artist', 'Unknown'),
                'l': metadata.get('album', 'Unknown'),
                'c': 0,
            }

        entry = youtube[video_id][c_type]

        if abs_path not in entry['paths']:
            entry['paths'].append(abs_path)

        entry['c'] = entry.get('c', 0) + 1
        entry['t'] = metadata.get('title', entry.get('t'))
        entry['a'] = metadata.get('artist', entry.get('a'))

        if spotify_id:
            entry['s'] = spotify_id
            spotify_index[spotify_id] = video_id

        self.save()

    @trace
    def check_existing(self, video_id=None, content_type=None, target_folder=None, spotify_id=None):
        if not content_type:
            return False, None

        c_type = 'audio' if 'audio' in content_type.lower() or 'music' in content_type.lower() else 'video'
        abs_target_folder = os.path.abspath(target_folder) if target_folder else ""

        youtube = self.data.get("youtube", {})
        spotify_index = self.data.get("spotify", {})

        found_vid = None
        if video_id and video_id in youtube:
            found_vid = video_id

        if found_vid is None and spotify_id and spotify_id in spotify_index:
            found_vid = spotify_index[spotify_id]

        if found_vid and c_type in youtube.get(found_vid, {}):
            return self._check_entry_paths(
                youtube[found_vid][c_type], found_vid, c_type, abs_target_folder,
            )

        return False, None

    def _check_entry_paths(self, entry, video_id, c_type, abs_target_folder):
        stored_paths = entry.get('paths', [])
        valid_paths = []
        found_in_target = False
        found_path_str = ""

        for path in stored_paths:
            if os.path.exists(path):
                valid_paths.append(path)
                file_dir = os.path.dirname(path)
                if file_dir == abs_target_folder:
                    found_in_target = True
                    found_path_str = path

        if len(valid_paths) != len(stored_paths):
            entry['paths'] = valid_paths
            if not valid_paths:
                del self.data["youtube"][video_id][c_type]
                if not self.data["youtube"][video_id]:
                    del self.data["youtube"][video_id]
            self.save()

        if found_in_target:
            return True, {
                'file_path': found_path_str,
                'title': entry.get('t'),
                'artist': entry.get('a'),
            }

        return False, None

    def update_path(self, old_path, new_path):
        old_abs = os.path.abspath(old_path)
        new_abs = os.path.abspath(new_path)

        updated = False
        youtube = self.data.get("youtube", {})

        for vid, data in youtube.items():
            for c_type, entry in data.items():
                if 'paths' in entry:
                    if old_abs in entry['paths']:
                        entry['paths'] = [p for p in entry['paths'] if p != old_abs]
                        if new_abs not in entry['paths']:
                            entry['paths'].append(new_abs)
                        updated = True

        if updated:
            self.save()

    def reset(self):
        self.data = {"youtube": {}, "spotify": {}}
        if os.path.exists(REGISTRY_PATH):
            try:
                os.remove(REGISTRY_PATH)
            except OSError:
                pass


registry = RegistryManager()
