import json
from pathlib import Path

from django.core.management.base import BaseCommand

from game.models import Question

DEFAULT_FILE = Path(__file__).resolve().parents[2] / "data" / "questions.json"


class Command(BaseCommand):
    help = "Add questions from a JSON file. Questions already in the database are left as they are."

    def add_arguments(self, parser):
        parser.add_argument("file", nargs="?", default=DEFAULT_FILE, type=Path)

    def handle(self, *args, **options):
        questions = json.loads(options["file"].read_text(encoding="utf-8"))

        created = 0
        for item in questions:
            # The text identifies a question: running the command twice adds no duplicates,
            # and questions edited in the admin are never overwritten.
            _, was_created = Question.objects.get_or_create(
                text=item["text"],
                defaults={"answer": item["answer"], "category": item.get("category", "")},
            )
            created += was_created

        skipped = len(questions) - created
        self.stdout.write(
            self.style.SUCCESS(f"{created} questions added, {skipped} already existed.")
        )
