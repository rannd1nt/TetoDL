# core/registry.py
import os
import json
from ..constants import REGISTRY_PATH

class RegistryManager:
    def __init__(self):
        self.data = {}
        self.load()

    def load(self):
        if os.path.exists(REGISTRY_PATH):
            try:
                with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}

    def save(self):
        try:
            with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, separators=(',', ':'))
        except Exception:
            pass

    def register_download(self, video_id, file_path, content_type, metadata):
        if not video_id or not content_type: return

        c_type = 'audio' if 'audio' in content_type.lower() or 'music' in content_type.lower() else 'video'
        
        abs_path = os.path.abspath(file_path)

        if video_id not in self.data:
            self.data[video_id] = {}
        
        if c_type not in self.data[video_id]:
            self.data[video_id][c_type] = {
                'paths': [],
                't': metadata.get('title', 'Unknown'),
                'a': metadata.get('artist', 'Unknown'),
                'l': metadata.get('album', 'Unknown'),
                'c': 0
            }

        entry = self.data[video_id][c_type]
        
        # Add new path if doesnt exist
        if abs_path not in entry['paths']:
            entry['paths'].append(abs_path)
        
        # Update metadata & counter
        entry['c'] = entry.get('c', 0) + 1
        entry['t'] = metadata.get('title', entry.get('t'))
        entry['a'] = metadata.get('artist', entry.get('a'))
        
        self.save()

    def check_existing(self, video_id, content_type, target_folder):
        """
        Cek apakah ID ini ada file fisiknya di folder target spesifik?
        Sekaligus membersihkan path sampah (file yg udah dihapus user).
        
        Returns:
            (bool, dict_metadata_if_found)
        """
        if not video_id or video_id not in self.data:
            return False, None

        c_type = 'audio' if 'audio' in content_type.lower() or 'music' in content_type.lower() else 'video'
        
        if c_type not in self.data[video_id]:
            return False, None

        entry = self.data[video_id][c_type]
        stored_paths = entry.get('paths', [])
        
        abs_target_folder = os.path.abspath(target_folder)
        
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
            else:
                pass


        if len(valid_paths) != len(stored_paths):
            entry['paths'] = valid_paths
            if not valid_paths:
                del self.data[video_id][c_type]
                if not self.data[video_id]:
                    del self.data[video_id]
            self.save()

        if found_in_target:
            return True, {
                'file_path': found_path_str,
                'title': entry.get('t'),
                'artist': entry.get('a')
            }
        
        return False, None
    
    def update_path(self, old_path, new_path):
        """
        Update registered path from old location to new location.
        Used when moving files after sharing (Staging -> Parent).
        """
        old_abs = os.path.abspath(old_path)
        new_abs = os.path.abspath(new_path)
        
        updated = False
        
        for vid, data in self.data.items():
            for c_type, entry in data.items():
                if 'paths' in entry:
                    if old_abs in entry['paths']:
                        entry['paths'] = [p for p in entry['paths'] if p != old_abs]
                        
                        if new_abs not in entry['paths']:
                            entry['paths'].append(new_abs)
                        
                        updated = True
                        
        if updated:
            self.save()

registry = RegistryManager()