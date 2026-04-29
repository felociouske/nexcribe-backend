"""
python manage.py seed_transcription_tasks
python manage.py seed_transcription_tasks --count 40

Fetches real audiobook chapters from the LibriVox public API and seeds them
as TranscriptionTask rows. Each task has a direct MP3 stream URL so users
can listen inline without downloading.

LibriVox API docs: https://librivox.org/api/info
All audio is public domain — free to use.
"""
import time
import logging
import urllib.request
import json

from django.core.management.base import BaseCommand
from apps.transcription.models import TranscriptionTask

logger = logging.getLogger(__name__)

# Hand-picked LibriVox book IDs — short chapters, clear narration, varied topics
# These are well-known public domain books with high audio quality
BOOK_IDS = [
    '127',    # Pride and Prejudice
    '10',     # Alice in Wonderland
    '9',      # Treasure Island
    '29',     # The Adventures of Tom Sawyer
    '61',     # A Tale of Two Cities
    '74',     # The Picture of Dorian Gray
    '84',     # Frankenstein
    '98',     # Around the World in 80 Days
    '158',    # The Jungle Book
    '174',    # Anne of Green Gables
    '196',    # The Time Machine
    '209',    # The War of the Worlds
    '254',    # Great Expectations
    '268',    # Jane Eyre
    '281',    # The Secret Garden
    '310',    # Wuthering Heights
    '345',    # Dracula
    '391',    # Sherlock Holmes: The Adventures
    '420',    # Twenty Thousand Leagues
    '512',    # The Count of Monte Cristo
]

# Pay scale based on duration
def get_pay_kes(duration_seconds):
    minutes = duration_seconds / 60
    if minutes <= 5:
        return 150
    elif minutes <= 10:
        return 280
    elif minutes <= 20:
        return 500
    elif minutes <= 30:
        return 750
    else:
        return 1000

def get_difficulty(duration_seconds):
    minutes = duration_seconds / 60
    if minutes <= 5:
        return 'BASIC'
    elif minutes <= 10:
        return 'EASY'
    elif minutes <= 20:
        return 'MEDIUM'
    else:
        return 'HARD'

def get_plan_level(duration_seconds):
    # All tasks accessible at level 1 — difficulty already gates complexity
    return 1


class Command(BaseCommand):
    help = 'Seed transcription tasks from LibriVox public domain audiobooks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count', type=int, default=30,
            help='Number of tasks to create (default: 30)'
        )
        parser.add_argument(
            '--max-minutes', type=int, default=25,
            help='Only include chapters shorter than this many minutes (default: 25)'
        )

    def handle(self, *args, **options):
        target_count = options['count']
        max_seconds = options['max_minutes'] * 60

        created = 0
        skipped = 0
        errors = 0

        self.stdout.write(f'Fetching audio chapters from LibriVox API...')

        for book_id in BOOK_IDS:
            if created >= target_count:
                break

            try:
                url = f'https://librivox.org/api/feed/audiobooks/id/{book_id}?format=json'
                req = urllib.request.Request(url, headers={'User-Agent': 'Nexcribe/1.0'})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode())

                book = data.get('books', [None])[0]
                if not book:
                    continue

                book_title = book.get('title', 'Unknown').strip()
                book_author_first = book.get('authors', [{}])[0].get('first_name', '') if book.get('authors') else ''
                book_author_last = book.get('authors', [{}])[0].get('last_name', '') if book.get('authors') else ''
                book_author = f'{book_author_first} {book_author_last}'.strip()
                language = book.get('language', 'English')

                # Fetch sections (chapters) for this book
                sections_url = f'https://librivox.org/api/feed/audiotracks?project_id={book_id}&format=json'
                req2 = urllib.request.Request(sections_url, headers={'User-Agent': 'Nexcribe/1.0'})
                with urllib.request.urlopen(req2, timeout=10) as resp2:
                    sections_data = json.loads(resp2.read().decode())

                sections = sections_data.get('sections', [])
                if not sections:
                    continue

                for section in sections:
                    if created >= target_count:
                        break

                    listen_url = section.get('listen_url', '')
                    if not listen_url:
                        continue

                    # Parse duration — format is "HH:MM:SS" or "MM:SS"
                    duration_str = section.get('playtime', '0:00')
                    parts = duration_str.split(':')
                    try:
                        if len(parts) == 3:
                            duration_seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                        elif len(parts) == 2:
                            duration_seconds = int(parts[0]) * 60 + int(parts[1])
                        else:
                            duration_seconds = int(parts[0])
                    except (ValueError, IndexError):
                        continue

                    # Skip chapters that are too long or too short
                    if duration_seconds < 60 or duration_seconds > max_seconds:
                        skipped += 1
                        continue

                    section_num = section.get('section_number', '1')
                    chapter_title = section.get('title', f'Chapter {section_num}').strip()
                    title = f'{book_title} — {chapter_title}'

                    # Skip if already exists
                    if TranscriptionTask.objects.filter(audio_url=listen_url).exists():
                        skipped += 1
                        continue

                    TranscriptionTask.objects.create(
                        title=title[:200],
                        description=(
                            f'Transcribe this chapter from "{book_title}" by {book_author}. '
                            f'Type exactly what you hear — every word, including punctuation.'
                        ),
                        source=TranscriptionTask.SOURCE_LIBRIVOX,
                        difficulty=get_difficulty(duration_seconds),
                        language=language.capitalize() if language else 'English',
                        duration_seconds=duration_seconds,
                        pay_kes=get_pay_kes(duration_seconds),
                        minimum_plan_level=get_plan_level(duration_seconds),
                        audio_url=listen_url,
                        book_title=book_title[:200],
                        book_author=book_author[:200],
                        status=TranscriptionTask.STATUS_AVAILABLE,
                    )
                    created += 1
                    self.stdout.write(f'  [{created}] {title[:70]}... ({duration_seconds//60}m {duration_seconds%60}s)')

                # Be polite to the LibriVox API
                time.sleep(0.5)

            except Exception as e:
                errors += 1
                self.stdout.write(self.style.WARNING(f'  Book {book_id} failed: {e}'))
                continue

        self.stdout.write('')
        if created > 0:
            self.stdout.write(self.style.SUCCESS(
                f'Done — {created} transcription tasks created, {skipped} skipped, {errors} errors.'
            ))
            self.stdout.write(self.style.SUCCESS(
                f'Audio streams from LibriVox — users can play inline, no download needed.'
            ))
        else:
            self.stdout.write(self.style.ERROR(
                'No tasks created. Check your internet connection and try again.'
            ))