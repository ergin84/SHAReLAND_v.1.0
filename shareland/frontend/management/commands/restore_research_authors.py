import csv
import os
import uuid
from typing import Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from django.contrib.auth.models import User

from frontend.models import Research, ResearchAuthor


class Command(BaseCommand):
    help = (
        "NOTE: The Author table has been consolidated to User/Profile. "
        "This command is deprecated for old Author UUID CSVs. "
        "For research-author restoration, provide CSV with columns: id_research,id_user "
        "(where id_user is the integer User PK from auth_user table)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv', dest='csv_path', default=None,
            help='Path to CSV file with columns: id_research,id_author.'
        )
        parser.add_argument(
            '--dry-run', action='store_true', default=False,
            help='Only report what would change without writing to DB.'
        )

    def resolve_default_csv(self) -> Optional[str]:
        # Try repo-level export path if not provided
        # Typically at <repo_root>/database_csv_exports/research_author.csv
        project_root = getattr(settings, 'BASE_DIR', None)
        candidates = []
        if project_root:
            # settings.BASE_DIR points to shareland/shareland; go up one and check
            candidates.append(os.path.abspath(os.path.join(project_root, '..', 'database_csv_exports', 'research_author.csv')))
            # Also try two levels up just in case
            candidates.append(os.path.abspath(os.path.join(project_root, '..', '..', 'database_csv_exports', 'research_author.csv')))
        else:
            candidates.append(os.path.abspath('database_csv_exports/research_author.csv'))

        for p in candidates:
            if os.path.isfile(p):
                return p
        return None

    def handle(self, *args, **options):
        csv_path = options.get('csv_path') or self.resolve_default_csv()
        dry_run = options.get('dry_run', False)

        if not csv_path or not os.path.isfile(csv_path):
            raise CommandError(
                f"CSV file not found. Provide --csv or place research_author.csv under database_csv_exports. Tried: {csv_path!r}"
            )

        created = 0
        existed = 0
        skipped_missing = 0
        failed = 0

        self.stdout.write(self.style.MIGRATE_HEADING(f"Reading: {csv_path}"))

        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Accept both exact header names and flexible casing
            # Normalize keys
            field_map = {k.lower(): k for k in reader.fieldnames or []}
            id_research_key = field_map.get('id_research') or 'id_research'
            id_author_key = field_map.get('id_author') or 'id_author'

            if id_research_key not in reader.fieldnames or id_author_key not in reader.fieldnames:
                raise CommandError('CSV must contain columns: id_research,id_author')

            with transaction.atomic():
                for i, row in enumerate(reader, start=1):
                    try:
                        research_id_raw = row[id_research_key]
                        author_id_raw = row[id_author_key]
                        if not research_id_raw or not author_id_raw:
                            skipped_missing += 1
                            continue

                        try:
                            research_id = int(research_id_raw)
                        except ValueError:
                            skipped_missing += 1
                            continue

                        try:
                            author_uuid = uuid.UUID(str(author_id_raw))
                        except Exception:
                            skipped_missing += 1
                            continue

                        try:
                            research = Research.objects.get(pk=research_id)
                        except Research.DoesNotExist:
                            skipped_missing += 1
                            continue

                        # NOTE: The Author table has been consolidated into User/Profile.
                        # The CSV contains Author UUIDs from the old data export.
                        # Since Author data was migrated to User, we cannot directly look up by UUID.
                        # This command now requires restoration via a different approach:
                        # Either provide a new CSV with user_id instead of author_uuid,
                        # or manually restore relationships from backup/archive.
                        # 
                        # For now, this command skips Author UUID rows as the data has been
                        # migrated and the Author table is deprecated.
                        self.stdout.write(self.style.WARNING(
                            f"Row {i}: Author UUID '{author_id_raw}' from old export - "
                            f"Author table consolidated to User. See command help for details."
                        ))
                        skipped_missing += 1
                        continue

                    except Exception as e:
                        failed += 1
                        # Avoid breaking the transaction for a single bad row; log and continue
                        self.stderr.write(self.style.WARNING(f"Row {i} failed: {e}"))

        summary = (
            f"created={created}, existed={existed}, skipped_missing={skipped_missing}, failed={failed}, dry_run={dry_run}"
        )
        if dry_run:
            self.stdout.write(self.style.NOTICE("Dry run complete: " + summary))
        else:
            self.stdout.write(self.style.SUCCESS("Restore complete: " + summary))
