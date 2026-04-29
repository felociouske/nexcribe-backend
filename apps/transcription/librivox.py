"""
LibriVox API integration for fetching public domain audiobook sections
as transcription tasks. No audio files are stored — only the streaming URL
and metadata are saved in the database.

LibriVox API docs: https://librivox.org/api/info
"""
import requests
import logging

logger = logging.getLogger(__name__)

LIBRIVOX_API_BASE = 'https://librivox.org/api/feed'
LIBRIVOX_AUDIO_BASE = 'https://www.archive.org/download'


def fetch_librivox_books(limit=20, offset=0, language='English'):
    """Fetch a list of audiobooks from LibriVox API."""
    try:
        resp = requests.get(
            f'{LIBRIVOX_API_BASE}/audiobooks',
            params={
                'format': 'json',
                'fields': 'id,title,url_zip_file,authors,language,sections',
                'limit': limit,
                'offset': offset,
                'language': language,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get('books', [])
    except Exception as e:
        logger.error(f'LibriVox book fetch error: {e}')
        return []


def fetch_librivox_sections(book_id):
    """Fetch individual audio sections (chapters) for a book."""
    try:
        resp = requests.get(
            f'{LIBRIVOX_API_BASE}/audiotracks',
            params={
                'format': 'json',
                'fields': 'id,section_number,title,playtime,listen_url,reader',
                'project_id': book_id,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get('sections', [])
    except Exception as e:
        logger.error(f'LibriVox sections fetch error: {e}')
        return []


def parse_playtime_to_seconds(playtime_str):
    """Convert 'MM:SS' or 'HH:MM:SS' to total seconds."""
    try:
        parts = playtime_str.strip().split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except Exception:
        pass
    return 0


def difficulty_from_duration(seconds):
    """Auto-assign difficulty based on audio length."""
    minutes = seconds / 60
    if minutes <= 5:
        return 'BASIC'
    elif minutes <= 15:
        return 'EASY'
    elif minutes <= 30:
        return 'MEDIUM'
    else:
        return 'HARD'


def pay_from_duration(seconds):
    """Auto-calculate pay in KES based on audio length."""
    minutes = seconds / 60
    if minutes <= 5:
        return 300
    elif minutes <= 10:
        return 600
    elif minutes <= 20:
        return 1000
    elif minutes <= 30:
        return 1500
    elif minutes <= 45:
        return 2200
    elif minutes <= 60:
        return 3500
    elif minutes <= 90:
        return 5500
    else:
        return 9000


def min_plan_from_duration(seconds):
    """Auto-assign minimum plan level based on duration."""
    minutes = seconds / 60
    if minutes <= 5:
        return 1
    elif minutes <= 10:
        return 2
    elif minutes <= 20:
        return 3
    elif minutes <= 30:
        return 4
    elif minutes <= 45:
        return 5
    elif minutes <= 60:
        return 6
    elif minutes <= 90:
        return 7
    else:
        return 8
