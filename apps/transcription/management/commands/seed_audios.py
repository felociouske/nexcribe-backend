import random
from django.core.management.base import BaseCommand
from apps.transcription.models import TranscriptionTask


# Real LibriVox public domain audio URLs (archive.org hosted)
AUDIO_TASKS = [
    {
        'title': 'The Adventures of Tom Sawyer — Chapter 1',
        'book_title': 'The Adventures of Tom Sawyer',
        'book_author': 'Mark Twain',
        'audio_url': 'https://www.archive.org/download/tom_sawyer_librivox/tomsawyer_01_twain_64kb.mp3',
        'duration_seconds': 420,
    },
    {
        'title': 'Pride and Prejudice — Chapter 1',
        'book_title': 'Pride and Prejudice',
        'book_author': 'Jane Austen',
        'audio_url': 'https://www.archive.org/download/pride_and_prejudice_librivox/prideprejudice_01_austen_64kb.mp3',
        'duration_seconds': 380,
    },
    {
        'title': 'Sherlock Holmes — A Scandal in Bohemia Part 1',
        'book_title': 'The Adventures of Sherlock Holmes',
        'book_author': 'Arthur Conan Doyle',
        'audio_url': 'https://www.archive.org/download/adventures_of_sherlock_holmes_librivox/adventuresherlockholmes_01_doyle_64kb.mp3',
        'duration_seconds': 510,
    },
    {
        'title': 'Alice in Wonderland — Down the Rabbit Hole',
        'book_title': 'Alice in Wonderland',
        'book_author': 'Lewis Carroll',
        'audio_url': 'https://www.archive.org/download/alices_adventures_in_wonderland_librivox/aliceinwonderland_01_carroll_64kb.mp3',
        'duration_seconds': 360,
    },
    {
        'title': 'The Great Gatsby — Chapter 1',
        'book_title': 'The Great Gatsby',
        'book_author': 'F. Scott Fitzgerald',
        'audio_url': 'https://www.archive.org/download/the_great_gatsby_librivox/greatgatsby_1_fitzgerald_64kb.mp3',
        'duration_seconds': 490,
    },
    {
        'title': 'Moby Dick — Chapter 1: Loomings',
        'book_title': 'Moby Dick',
        'book_author': 'Herman Melville',
        'audio_url': 'https://www.archive.org/download/moby_dick_librivox/mobydick_001_melville_64kb.mp3',
        'duration_seconds': 540,
    },
    {
        'title': 'Frankenstein — Letter 1',
        'book_title': 'Frankenstein',
        'book_author': 'Mary Shelley',
        'audio_url': 'https://www.archive.org/download/frankenstein_librivox/frankenstein_01_shelley_64kb.mp3',
        'duration_seconds': 320,
    },
    {
        'title': 'Dracula — Chapter 1: Jonathan Harkers Journal',
        'book_title': 'Dracula',
        'book_author': 'Bram Stoker',
        'audio_url': 'https://www.archive.org/download/dracula_0809_librivox/dracula_01_stoker_64kb.mp3',
        'duration_seconds': 600,
    },
    {
        'title': 'The Picture of Dorian Gray — Chapter 1',
        'book_title': 'The Picture of Dorian Gray',
        'book_author': 'Oscar Wilde',
        'audio_url': 'https://www.archive.org/download/dorian_gray_librivox/doriangray_01_wilde_64kb.mp3',
        'duration_seconds': 440,
    },
    {
        'title': 'Romeo and Juliet — Act 1 Scene 1',
        'book_title': 'Romeo and Juliet',
        'book_author': 'William Shakespeare',
        'audio_url': 'https://www.archive.org/download/romeo_and_juliet_librivox/romeoandjuliet_01_shakespeare_64kb.mp3',
        'duration_seconds': 480,
    },
    {
        'title': 'War and Peace — Book 1 Chapter 1',
        'book_title': 'War and Peace',
        'book_author': 'Leo Tolstoy',
        'audio_url': 'https://www.archive.org/download/war_and_peace_librivox/warandpeace_01_tolstoy_64kb.mp3',
        'duration_seconds': 720,
    },
    {
        'title': 'A Tale of Two Cities — Chapter 1',
        'book_title': 'A Tale of Two Cities',
        'book_author': 'Charles Dickens',
        'audio_url': 'https://www.archive.org/download/tale_two_cities_librivox/taletwocities_01_dickens_64kb.mp3',
        'duration_seconds': 400,
    },
    {
        'title': 'The Jungle Book — Mowglis Brothers',
        'book_title': 'The Jungle Book',
        'book_author': 'Rudyard Kipling',
        'audio_url': 'https://www.archive.org/download/jungle_book_librivox/junglebook_01_kipling_64kb.mp3',
        'duration_seconds': 560,
    },
    {
        'title': 'Don Quixote — Chapter 1',
        'book_title': 'Don Quixote',
        'book_author': 'Miguel de Cervantes',
        'audio_url': 'https://www.archive.org/download/don_quixote_librivox/donquixote_01_cervantes_64kb.mp3',
        'duration_seconds': 350,
    },
    {
        'title': 'The Odyssey — Book 1',
        'book_title': 'The Odyssey',
        'book_author': 'Homer',
        'audio_url': 'https://www.archive.org/download/the_odyssey_librivox/odyssey_01_homer_64kb.mp3',
        'duration_seconds': 650,
    },
    {
        'title': 'Anna Karenina — Part 1 Chapter 1',
        'book_title': 'Anna Karenina',
        'book_author': 'Leo Tolstoy',
        'audio_url': 'https://www.archive.org/download/anna_karenina_librivox/annakarenina_01_tolstoy_64kb.mp3',
        'duration_seconds': 410,
    },
    {
        'title': 'Crime and Punishment — Part 1 Chapter 1',
        'book_title': 'Crime and Punishment',
        'book_author': 'Fyodor Dostoevsky',
        'audio_url': 'https://www.archive.org/download/crime_and_punishment_librivox/crimeandpunishment_01_dostoevsky_64kb.mp3',
        'duration_seconds': 470,
    },
    {
        'title': 'Wuthering Heights — Chapter 1',
        'book_title': 'Wuthering Heights',
        'book_author': 'Emily Bronte',
        'audio_url': 'https://www.archive.org/download/wuthering_heights_librivox/wutheringheights_01_bronte_64kb.mp3',
        'duration_seconds': 430,
    },
    {
        'title': 'The Count of Monte Cristo — Chapter 1',
        'book_title': 'The Count of Monte Cristo',
        'book_author': 'Alexandre Dumas',
        'audio_url': 'https://www.archive.org/download/count_of_monte_cristo_librivox/montecristo_01_dumas_64kb.mp3',
        'duration_seconds': 520,
    },
    {
        'title': 'Treasure Island — Chapter 1',
        'book_title': 'Treasure Island',
        'book_author': 'Robert Louis Stevenson',
        'audio_url': 'https://www.archive.org/download/treasure_island_librivox/treasureisland_01_stevenson_64kb.mp3',
        'duration_seconds': 390,
    },
]


def duration_to_difficulty(secs):
    m = secs / 60
    if m <= 5: return 'BASIC'
    if m <= 10: return 'EASY'
    if m <= 20: return 'MEDIUM'
    return 'HARD'


def duration_to_pay(secs):
    m = secs / 60
    if m <= 5: return 300
    if m <= 10: return 600
    if m <= 20: return 1000
    if m <= 30: return 1500
    if m <= 45: return 2200
    if m <= 60: return 3500
    return 5500


def duration_to_level(secs):
    m = secs / 60
    if m <= 5: return 1
    if m <= 10: return 2
    if m <= 20: return 3
    if m <= 30: return 4
    if m <= 45: return 5
    if m <= 60: return 6
    return 7


class Command(BaseCommand):
    help = 'Seed transcription tasks with real LibriVox audio URLs'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=20,
                            help='Number of tasks to create (will loop through audio list)')

    def handle(self, *args, **options):
        count = options['count']
        created = 0
        skipped = 0

        for i in range(count):
            task_data = AUDIO_TASKS[i % len(AUDIO_TASKS)]
            title = task_data['title']

            # Add variation if looping
            if i >= len(AUDIO_TASKS):
                title = f"{task_data['title']} (Part {(i // len(AUDIO_TASKS)) + 1})"

            if TranscriptionTask.objects.filter(title=title).exists():
                skipped += 1
                continue

            duration = task_data['duration_seconds'] + random.randint(-60, 60)
            duration = max(120, duration)

            TranscriptionTask.objects.create(
                title=title,
                description=f"Transcribe this audio excerpt from \"{task_data['book_title']}\" by {task_data['book_author']}. Type exactly what you hear, including punctuation.",
                source=TranscriptionTask.SOURCE_LIBRIVOX,
                difficulty=duration_to_difficulty(duration),
                language='English',
                duration_seconds=duration,
                pay_kes=duration_to_pay(duration),
                minimum_plan_level=duration_to_level(duration),
                librivox_id=str(i),
                librivox_section_id=str(i * 10),
                audio_url=task_data['audio_url'],
                book_title=task_data['book_title'],
                book_author=task_data['book_author'],
                status=TranscriptionTask.STATUS_AVAILABLE,
            )
            created += 1
            self.stdout.write(f'  + {title}')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! {created} tasks created, {skipped} skipped. '
            f'Total: {TranscriptionTask.objects.count()}'
        ))