import json
from django.core.management.base import BaseCommand
from django.conf import settings
from candidates.models import Candidate
class Command(BaseCommand):
    help = 'Load candidates from a JSON dataset file into the database'
    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            default=settings.ML_DATASET_PATH,
            help='Path to JSON dataset file',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing candidates before loading',
        )
    def handle(self, *args, **options):
        path = options['path']
        if options['clear']:
            count = Candidate.objects.count()
            Candidate.objects.all().delete()
            self.stdout.write(f'Deleted {count} existing candidates')
        with open(path, 'r', encoding='utf-8') as f:
            candidates = json.load(f)
        created = 0
        skipped = 0
        for c in candidates:
            personal = c.get('personal', {})
            name = personal.get('name', 'Unknown')
            if Candidate.objects.filter(name=name).exists():
                skipped += 1
                continue
            Candidate.objects.create(
                name=name,
                age=personal.get('age', 0),
                city=personal.get('city', ''),
                region=personal.get('region', ''),
                school_type=personal.get('school_type', ''),
                has_mentor=personal.get('has_mentor', False),
                profile_data=c,
            )
            created += 1
        self.stdout.write(
            self.style.SUCCESS(
                f'Loaded {created} candidates ({skipped} skipped as duplicates)'
            )
        )
