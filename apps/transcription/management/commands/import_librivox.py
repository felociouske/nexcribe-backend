from django.core.management.base import BaseCommand
from apps.transcription.models import TranscriptionTask
from apps.transcription.librivox import (
    fetch_librivox_books, fetch_librivox_sections,
    parse_playtime_to_seconds, difficulty_from_duration,
    pay_from_duration, min_plan_from_duration,
)


class Command(BaseCommand):
    help = 'Import transcription tasks from LibriVox API'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=5, help='Number of books to fetch')
        parser.add_argument('--offset', type=int, default=0)
        parser.add_argument('--language', type=str, default='English')

    def handle(self, *args, **options):
        books = fetch_librivox_books(
            limit=options['limit'],
            offset=options['offset'],
            language=options['language'],
        )

        if not books:
            self.stdout.write(self.style.WARNING('No books returned from LibriVox API.'))
            return

        created = 0
        skipped = 0

        for book in books:
            book_id = str(book.get('id', ''))
            book_title = book.get('title', 'Unknown')
            authors = book.get('authors', [])
            author_name = authors[0].get('first_name', '') + ' ' + authors[0].get('last_name', '') if authors else 'Unknown'

            sections = fetch_librivox_sections(book_id)

            for section in sections[:3]:  # max 3 sections per book to avoid flooding
                section_id = str(section.get('id', ''))
                audio_url = section.get('listen_url', '')
                playtime = section.get('playtime', '0:00')
                duration_secs = parse_playtime_to_seconds(playtime)

                if not audio_url or duration_secs == 0:
                    skipped += 1
                    continue

                # Skip if already imported
                if TranscriptionTask.objects.filter(librivox_section_id=section_id).exists():
                    skipped += 1
                    continue

                section_title = section.get('title') or f'Section {section.get("section_number", "")}'
                title = f'{book_title} — {section_title.strip()}'

                TranscriptionTask.objects.create(
                    title=title[:200],
                    description=f'Transcribe this audio section from "{book_title}" by {author_name.strip()}.',
                    source=TranscriptionTask.SOURCE_LIBRIVOX,
                    difficulty=difficulty_from_duration(duration_secs),
                    language=options['language'],
                    duration_seconds=duration_secs,
                    pay_kes=pay_from_duration(duration_secs),
                    minimum_plan_level=min_plan_from_duration(duration_secs),
                    librivox_id=book_id,
                    librivox_section_id=section_id,
                    audio_url=audio_url,
                    book_title=book_title[:200],
                    book_author=author_name.strip()[:200],
                    status=TranscriptionTask.STATUS_AVAILABLE,
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f'LibriVox import complete: {created} tasks created, {skipped} skipped.'
        ))
