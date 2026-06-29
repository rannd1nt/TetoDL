"""
Cache system for metadata
"""
import os
import json
import time
import hashlib
from ..constants import CACHE_PATH
from ..utils.console import console
from ..utils.i18n_keys import Keys


def load_cache():
    """Load cache metadata from file"""
    if not os.path.exists(CACHE_PATH):
        return {}
    
    try:
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(cache_data):
    """Save cache metadata to file"""
    try:
        with open(CACHE_PATH, "w") as f:
            json.dump(cache_data, f, indent=2)
    except Exception:
        console.err(Keys.core.failed_save_cache)

def reset_cache():
    """Clear and reset all cache metadata"""
    try:
        if os.path.exists(CACHE_PATH):
            os.remove(CACHE_PATH)
            return True
        return True
    except Exception as e:
        console.err(Keys.core.failed_delete_cache(error=e))
        return False

def get_url_hash(url: str):
    """Generate hash for URL as cache key"""
    return hashlib.md5(url.encode()).hexdigest()


def get_cached_metadata(url):
    """Get metadata from cache if available"""
    cache = load_cache()
    url_hash = get_url_hash(url)
    return cache.get(url_hash)

def get_cache_size():
    """Get cache size with human readable formatting"""
    try:
        if os.path.exists(CACHE_PATH):
            size = os.path.getsize(CACHE_PATH)
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size/1024:.1f} KB"
            else:
                return f"{size/(1024*1024):.1f} MB"
        return "0 B"
    except Exception:
        return "Unknown"

def cache_metadata(url, metadata):
    """Save metadata to cache"""
    cache = load_cache()
    url_hash = get_url_hash(url)
    cache[url_hash] = {
        'metadata': metadata,
        'timestamp': time.time()
    }
    save_cache(cache)