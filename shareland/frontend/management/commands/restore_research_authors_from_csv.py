#!/usr/bin/env python
"""
Restore all research-author relationships from the CSV export.
Maps old Author UUIDs to new User IDs based on the username pattern created during migration.
"""
import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
import os

from frontend.models import Research, ResearchAuthor
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = (
        "Restore Research-Author relationships from CSV export. "
        "Maps Author UUIDs (from old table) to User IDs (from migration)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv', dest='csv_path', default=None,
            help='Path to CSV file with columns: id_research,id,id_author.'
        )
        parser.add_argument(
            '--dry-run', action='store_true', default=False,
            help='Only report what would change without writing to DB.'
        )

    def find_user_by_author_uuid(self, author_uuid):
        """
        Find User by author UUID.
        Migration 0014 created users with username pattern: author_{uuid_prefix}
        where uuid_prefix is first 8 chars of the UUID.
        Also tries to find by email pattern: author.{uuid_prefix}@shareland.local
        """
        uuid_prefix = author_uuid[:8]
        
        # Try by username first
        user = User.objects.filter(username=f'author_{uuid_prefix}').first()
        if user:
            return user
        
        # Try by email
        user = User.objects.filter(email__startswith=f'author.{uuid_prefix}').first()
        if user:
            return user
        
        return None

    def handle(self, *args, **options):
        csv_path = options.get('csv_path')
        dry_run = options.get('dry_run', False)

        if not csv_path:
            # Try default locations - CSV is outside Docker, so use mounted path
            csv_path = '/app/database_csv_exports/research_author.csv'
            if not os.path.isfile(csv_path):
                # Fallback to relative path
                csv_path = 'database_csv_exports/research_author.csv'

        if not os.path.isfile(csv_path):
            raise CommandError(f"CSV file not found: {csv_path}")

        created = 0
        existed = 0
        skipped = 0
        errors = 0
        uuid_to_user = {}  # Cache for UUID -> User mapping

        self.stdout.write(self.style.MIGRATE_HEADING(f"Reading: {csv_path}"))

        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            with transaction.atomic():
                for i, row in enumerate(rows, start=1):
                    try:
                        research_id = int(row['id_research'])
                        author_uuid = row['id_author'].strip()

                        # Get research
                        try:
                            research = Research.objects.get(pk=research_id)
                        except Research.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f"Row {i}: Research {research_id} not found, skipping"))
                            skipped += 1
                            continue

                        # Find user by author UUID (use cache)
                        if author_uuid not in uuid_to_user:
                            uuid_to_user[author_uuid] = self.find_user_by_author_uuid(author_uuid)

                        user = uuid_to_user[author_uuid]
                        if not user:
                            self.stdout.write(self.style.WARNING(f"Row {i}: Author {author_uuid} mapping not found, skipping"))
                            errors += 1
                            continue

                        if dry_run:
                            exists = ResearchAuthor.objects.filter(id_research=research, id_author=user).exists()
                            if exists:
                                existed += 1
                            else:
                                created += 1
                        else:
                            obj, was_created = ResearchAuthor.objects.get_or_create(
                                id_research=research,
                                id_author=user
                            )
                            if was_created:
                                created += 1
                            else:
                                existed += 1

                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"Row {i} error: {e}"))
                        errors += 1

        summary = (
            f"created={created}, existed={existed}, skipped={skipped}, errors={errors}, dry_run={dry_run}"
        )
        if dry_run:
            self.stdout.write(self.style.NOTICE("Dry run complete: " + summary))
        else:
            self.stdout.write(self.style.SUCCESS("Restoration complete: " + summary))
