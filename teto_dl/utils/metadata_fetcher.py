import requests
import re

def clean_title_for_search(title):
    """
    Membersihkan judul dari sampah [Official Video], (Lyrics), dll
    biar pencarian cover art lebih akurat.
    """
    title = re.sub(r'\[.*?\]', '', title)
    title = re.sub(r'\(.*?\)', '', title)
    remove_words = ['official video', 'lyrics', 'lyric video', 'music video', 'mv', 'full audio', 'official music video']
    for word in remove_words:
        title = title.replace(word, '', -1)
        title = re.sub(f'(?i){word}', '', title)
    
    return title.strip()

def fetch_cover(artist, title):
    """
    Search 1:1 High Res cover art from iTunes based on Artist & Title
    """
    try:
        clean_title = clean_title_for_search(title)
        term = f"{artist} {clean_title}"
        
        url = "https://itunes.apple.com/search"
        params = {
            'term': term,
            'media': 'music',
            'entity': 'song',
            'limit': 1
        }
        
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        if data['resultCount'] > 0:
            artwork_url = data['results'][0]['artworkUrl100']
            return artwork_url.replace('100x100bb', '600x600bb')
            
        return None
    except Exception as e:
        return None