import requests
import re

def clean_title_for_search(title, artist=""):
    """
    Membersihkan judul secara agresif untuk iTunes Search.
    """
    if not title: return ""
    
    title = re.sub(r'\[.*?\]', '', title)
    title = re.sub(r'\(.*?\)', '', title)

    remove_words = [
        'official video', 'official audio', 'lyrics', 'lyric video',
        'music video', 'mv', 'full audio', 'official music video',
        'full ver', 'full version', 'hq', 'hd', '4k', 'remastered',
        'sub thai', 'sub indo', 'eng sub'
    ]
    
    for word in remove_words:
        title = re.sub(f'(?i){re.escape(word)}', '', title)
        
    title = title.replace('-', ' ').replace('/', ' ').replace('|', ' ').replace('_', ' ')
    
    if artist and len(artist) > 2: 
        title = re.sub(f'(?i){re.escape(artist)}', '', title)

    title = re.sub(r'\s+', ' ', title).strip()
    
    return title

import requests
import re

# ... (Fungsi clean_title_for_search TETAP SAMA, tidak perlu diubah) ...
def clean_title_for_search(title, artist=""):
    # (Biarkan kode cleaning kamu yang sudah kuat tadi disini)
    if not title: return ""
    title = re.sub(r'\[.*?\]', '', title)
    title = re.sub(r'\(.*?\)', '', title)
    remove_words = ['official video', 'official audio', 'lyrics', 'lyric video', 'music video', 'mv', 'full audio', 'official music video', 'full ver', 'full version', 'hq', 'hd', '4k', 'remastered', 'sub thai', 'sub indo', 'eng sub']
    for word in remove_words:
        title = re.sub(f'(?i){re.escape(word)}', '', title)
    title = title.replace('-', ' ').replace('/', ' ').replace('|', ' ').replace('_', ' ')
    if artist and len(artist) > 2:
        title = re.sub(f'(?i){re.escape(artist)}', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def fetch_cover(artist, title):
    """
    Search iTunes and return Metadata Dict + High Res Cover
    """
    try:
        clean_artist = artist.replace(' - Topic', '').strip()
        clean_title = clean_title_for_search(title, artist=clean_artist)
        if not clean_title: clean_title = title

        term = f"{clean_artist} {clean_title}"
        
        url = "https://itunes.apple.com/search"
        params = {'term': term, 'media': 'music', 'entity': 'song', 'limit': 1}
        
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        if data['resultCount'] > 0:
            result = data['results'][0]
            artwork = result['artworkUrl100'].replace('100x100bb', '600x600bb')
            
            return {
                'url': artwork,
                'artist': result.get('artistName'),
                'album': result.get('collectionName'),
                'title': result.get('trackName'),
                'date': result.get('releaseDate', '')[:4]
            }
            
        return None
    except Exception:
        return None