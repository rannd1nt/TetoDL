import requests
import re
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from typing import Optional, Dict, Any, Generator

from .styles import print_info

class MetadataFetcher:
    """
    Centralized fetcher for Cover Art (iTunes) and Lyrics (Genius).
    
    This class provides a unified interface to retrieve music metadata, 
    utilizing iTunes as the primary source for high-quality cover art and tags, 
    and Genius as a fallback or enrichment source for lyrics and additional details.
    """
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    @staticmethod
    def _clean_title(title: str, artist: str = "") -> str:
        """
        Sanitizes the song title by removing noise to extract the 'Core Title'.
        
        Removes brackets, official video tags, feature credits, and other 
        common YouTube title clutter to improve search accuracy.
        """
        if not title: return ""
        
        # Remove brackets and enclosed content
        title = re.sub(r'【.*?】', '', title)
        title = re.sub(r'\[.*?\]', '', title)
        title = re.sub(r'\(.*?\)', '', title)
        title = re.sub(r'「.*?」', '', title)
        title = re.sub(r'『.*?』', '', title)

        remove_words = [
            'official video', 'official audio', 'lyrics', 'lyric video',
            'music video', 'mv', 'full audio', 'official music video',
            'full ver', 'full version', 'hq', 'hd', '4k', 'remastered',
            'sub thai', 'sub indo', 'eng sub', 'live', 'video clip',
            'cover', 'self cover', 'synthesizer v', 'vocaloid',
            'feat.', 'ft.', 'featuring'
        ]
        
        for word in remove_words:
            title = re.sub(f'(?i){re.escape(word)}', '', title)
            
        clean_base = title.replace('-', ' ').replace('/', ' ').replace('|', ' ').replace('_', ' ').replace('×', ' ')
        
        if artist and len(artist) > 2:
            clean_base = re.sub(f'(?i){re.escape(artist)}', '', clean_base)

        clean_base = re.sub(r'\s+', ' ', clean_base).strip()
        return clean_base

    def _get_search_queries(self, artist: str, title: str, force_romaji: bool = False) -> Generator[str, None, None]:
        """
        Generates a sequence of search query variations to maximize hit rate.
        """
        clean_artist = artist.replace(' - Topic', '').strip()
        clean_title = self._clean_title(title, artist=clean_artist)
        
        if force_romaji:
            yield f"{clean_artist} {clean_title} Romanized"
            yield f"{clean_title} Romanized"
        
        yield f"{clean_artist} {clean_title}"
        
        separators = r'\s*(?:/|-|\||×)\s*'
        parts = re.split(separators, title)
        
        if len(parts) > 1:
            candidate = self._clean_title(parts[0], artist)
            if len(candidate) > 1:
                yield f"{clean_artist} {candidate}"
                yield candidate

        yield clean_title

    def _is_valid_match(
        self, 
        search_title: str, 
        result_title: str, 
        search_artist: Optional[str] = None, 
        result_artist: Optional[str] = None, 
        threshold: float = 0.4
    ) -> bool:
        """
        Validates if the search result matches the target using fuzzy logic.
        Checks Title similarity AND Artist similarity (if provided).
        """
        def normalize(s):
            return re.sub(r'[\W_]+', '', s.lower()) if s else ""
        
        s1 = normalize(search_title)
        s2 = normalize(result_title)
        
        if not s1 or not s2: return False
        
        title_match = False
        if s1 in s2 or s2 in s1:
            title_match = True
        elif SequenceMatcher(None, s1, s2).ratio() >= threshold:
            title_match = True
            
        if not title_match:
            return False

        if search_artist and result_artist:
            a1 = normalize(search_artist)
            a2 = normalize(result_artist)
            
            if len(a1) < 2 or len(a2) < 2: return True
            
            is_artist_match = False
            if a1 in a2 or a2 in a1:
                is_artist_match = True
            elif SequenceMatcher(None, a1, a2).ratio() >= 0.6:
                is_artist_match = True
            
            if not is_artist_match:
                return False
            
            return True

        return True

    def _clean_genius_lyrics(self, lyrics_text: str) -> str:
        """
        Cleans raw lyrics text scraped from Genius HTML.
        Removes headers, contributors, embeddings, and ad text.
        """
        if not lyrics_text: return ""
        
        match = re.search(r'\[', lyrics_text)
        if match:
            lyrics_text = lyrics_text[match.start():]
        else:
            lyrics_text = re.sub(r'^\d+\s*Contributors.*?Lyrics\s*', '', lyrics_text, flags=re.DOTALL | re.IGNORECASE)

        # Cleanup Standard Junk
        lyrics_text = re.sub(r'^Translations.*?Lyrics\s*', '', lyrics_text, flags=re.DOTALL | re.IGNORECASE)
        lyrics_text = re.sub(r'\d*Embed$', '', lyrics_text)
        lyrics_text = re.sub(r'You might also like.*', '', lyrics_text, flags=re.DOTALL | re.IGNORECASE)
        lyrics_text = re.sub(r'Get tickets as low as.*', '', lyrics_text, flags=re.DOTALL | re.IGNORECASE)
        lyrics_text = re.sub(r'\n{3,}', '\n\n', lyrics_text).strip()
        return lyrics_text

    
    def fetch_cover_itunes(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """
        Queries iTunes API for High-Res Cover Art and detailed metadata.
        Returns a dictionary containing artwork URL and tags if found.
        """
        try:
            clean_artist = artist.replace(' - Topic', '').strip()
            clean_title = self._clean_title(title, artist=clean_artist)
            if not clean_title: clean_title = title

            target_compare_title = clean_title
            term = f"{clean_artist} {clean_title}"
            
            url = "https://itunes.apple.com/search"
            params = {'term': term, 'media': 'music', 'entity': 'song', 'limit': 10}
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if data['resultCount'] > 0:
                for result in data['results']:
                    itunes_title = result.get('trackName')
                    itunes_artist = result.get('artistName')
                    
                    if self._is_valid_match(target_compare_title, itunes_title, search_artist=clean_artist, result_artist=itunes_artist):
                        artwork = result['artworkUrl100'].replace('100x100bb', '600x600bb')
                        
                        release_date = result.get('releaseDate', '')
                        if release_date:
                            release_date = release_date.split('T')[0]

                        return {
                            'url': artwork,
                            'title': itunes_title,
                            'artist': result.get('artistName'),
                            'album': result.get('collectionName'),
                            'album_artist': result.get('collectionArtistName', result.get('artistName')),
                            'date': release_date,
                            'genre': result.get('primaryGenreName'),
                            'composer': result.get('composerName'),
                            'track_num': f"{result.get('trackNumber')}/{result.get('trackCount')}" if result.get('trackCount') else None,
                            'disc_num': f"{result.get('discNumber')}/{result.get('discCount')}" if result.get('discCount') else None,
                            'source': 'iTunes'
                        }
                return None
            return None
        except Exception:
            return None

    def fetch_cover_genius(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """
        Fallback/Enrichment: Searches Genius API for metadata.
        Useful when iTunes fails or to gather extra fields like Composers.
        """
        target_compare_title = self._clean_title(title, artist)
        clean_artist = artist.replace(' - Topic', '').strip()

        for query in self._get_search_queries(artist, title):
            try:
                # --- SEARCH ---
                search_url = "https://genius.com/api/search/multi"
                params = {'per_page': '5', 'q': query}
                
                resp = requests.get(search_url, params=params, headers=self.HEADERS, timeout=10)
                data = resp.json()
                
                hits = []
                if 'response' in data and 'sections' in data['response']:
                    for section in data['response']['sections']:
                        if section['type'] == 'song':
                            hits = section['hits']
                            break
                if not hits: continue

                best_hit_summary = None
                for hit in hits:
                    hit_result = hit['result']
                    hit_title = hit_result['title']
                    
                    hit_artist = "Unknown"
                    if 'primary_artist' in hit_result:
                        hit_artist = hit_result['primary_artist']['name']

                    if self._is_valid_match(
                        target_compare_title,
                        hit_title, 
                        search_artist=clean_artist,
                        result_artist=hit_artist
                    ):
                        best_hit_summary = hit_result
                        break
                if not best_hit_summary: continue

                # --- FETCH DETAILS ---
                song_id = best_hit_summary['id']
                details_url = f"https://genius.com/api/songs/{song_id}"
                
                details_resp = requests.get(details_url, headers=self.HEADERS, timeout=10)
                details_data = details_resp.json()
                
                song_details = {}
                if 'response' in details_data and 'song' in details_data['response']:
                    song_details = details_data['response']['song']

                # --- EXTRACT FULL METADATA ---
                artwork_url = song_details.get('song_art_image_url') or best_hit_summary.get('song_art_image_url')
                if not artwork_url: continue

                album_name = "Single"
                album_artist = None
                if song_details.get('album'):
                    album_name = song_details['album'].get('name', 'Single')
                    if song_details['album'].get('artist'):
                        album_artist = song_details['album']['artist'].get('name')

                composers = []
                if song_details.get('writer_artists'):
                    for writer in song_details['writer_artists']:
                        composers.append(writer.get('name'))
                composer_str = ", ".join(composers) if composers else None

                genre = "Genius Tag"
                if song_details.get('tags'):
                    for tag in song_details['tags']:
                        if tag['name'].lower() not in ['tracklist', 'cover', 'remix']:
                            genre = tag['name']
                            break

                return {
                    'url': artwork_url,
                    'title': song_details.get('title'),
                    'artist': song_details.get('primary_artist', {}).get('name'),
                    'album': album_name,
                    'album_artist': album_artist or song_details.get('primary_artist', {}).get('name'),
                    'date': song_details.get('release_date'), 
                    'genre': genre,
                    'composer': composer_str,
                    'source': 'Genius'
                }

            except Exception:
                continue
        return None

    def fetch_metadata(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """
        Orchestrates the metadata fetching strategy.
        
        1. Attempts to fetch from iTunes first (preferred for standardized tags).
        2. If iTunes succeeds, attempts to enrich data (composers, dates) via Genius.
        3. If iTunes fails, falls back completely to Genius.
        """
        
        itunes_data = self.fetch_cover_itunes(artist, title)

        if itunes_data:
            try:
                clean_artist = itunes_data.get('artist', artist)
                clean_title = itunes_data.get('title', title)
                
                genius_enrichment = self.fetch_cover_genius(clean_artist, clean_title)
                
                if genius_enrichment:
                    if genius_enrichment.get('composer'): 
                        itunes_data['composer'] = genius_enrichment['composer']
                    if genius_enrichment.get('genre') and genius_enrichment['genre'] != "Genius Tag":
                        itunes_data['genre'] = genius_enrichment['genre']
                    if genius_enrichment.get('date'):
                        itunes_data['date'] = genius_enrichment['date']
                    if genius_enrichment.get('album_artist'):
                        itunes_data['album_artist'] = genius_enrichment['album_artist']
                        
                    itunes_data['source'] = 'iTunes + Genius (Rich)'
            except Exception:
                pass
            
            return itunes_data

        else:
            return self.fetch_cover_genius(artist, title)

    def fetch_lyrics_genius(
        self, 
        artist: str, 
        title: str, 
        romaji: bool = False, 
        quiet: bool = False
    ) -> Optional[str]:
        """
        Scrapes lyrics from Genius.com.
        
        Features strict validation to ensure the lyrics match the requested 
        artist/title, and supports Romanized lyrics search for non-English tracks.
        """
        target_compare_title = self._clean_title(title, artist)
        clean_artist = artist.replace(' - Topic', '').strip()
        
        for query in self._get_search_queries(artist, title, romaji):
            try:
                search_url = "https://genius.com/api/search/multi"
                params = {'per_page': '5', 'q': query}
                
                resp = requests.get(search_url, params=params, headers=self.HEADERS, timeout=10)
                data = resp.json()
                
                hits = []
                if 'response' in data and 'sections' in data['response']:
                    for section in data['response']['sections']:
                        if section['type'] == 'song':
                            hits = section['hits']
                            break
                
                if not hits: continue
                
                valid_hits = []
                
                for h in hits:
                    result = h['result']
                    hit_title = result['title']
                    
                    hit_artist = "Unknown"
                    if 'primary_artist' in result and 'name' in result['primary_artist']:
                        hit_artist = result['primary_artist']['name']
                    
                    if self._is_valid_match(
                        target_compare_title, 
                        hit_title, 
                        search_artist=clean_artist, 
                        result_artist=hit_artist
                    ):
                        valid_hits.append(h)
                
                if not valid_hits:
                    continue

                target_url = None

                if romaji:
                    for hit in valid_hits:
                        if "Romanized" in hit['result']['title_with_featured']:
                            target_url = hit['result']['url']
                            if not quiet: print_info(f"Found Romanized lyrics: {hit['result']['title']}")
                            break
                
                if not target_url:
                    target_url = valid_hits[0]['result']['url']
                    if not quiet: print_info(f"Fetching lyrics from: {valid_hits[0]['result']['title']}")

                page_resp = requests.get(target_url, headers=self.HEADERS, timeout=10)
                soup = BeautifulSoup(page_resp.text, 'html.parser')
                lyrics_divs = soup.find_all("div", attrs={"data-lyrics-container": "true"})
                
                if lyrics_divs:
                    lyrics_text = ""
                    for div in lyrics_divs:
                        for br in div.find_all("br"): br.replace_with("\n")
                        lyrics_text += div.get_text() + "\n\n"
                    
                    return self._clean_genius_lyrics(lyrics_text)
                    
            except Exception:
                continue

        return None

fetcher = MetadataFetcher()