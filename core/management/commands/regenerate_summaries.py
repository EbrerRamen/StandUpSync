from django.core.management.base import BaseCommand
from core.models import StandUpEntry
from core.utils import format_standup_summary, generate_summary
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Regenerates AI summaries for all standup entries'

    def handle(self, *args, **options):
        entries = StandUpEntry.objects.all()
        self.stdout.write(f"Found {entries.count()} entries to process")
        
        for entry in entries:
            self.stdout.write(f"Processing entry {entry.id}...")
            formatted_text = format_standup_summary(entry)
            summary = generate_summary(formatted_text)
            if summary:
                entry.ai_summary = summary
                entry.save()
                self.stdout.write(self.style.SUCCESS(f"Generated summary for entry {entry.id}"))
            else:
                self.stdout.write(self.style.ERROR(f"Failed to generate summary for entry {entry.id}")) 