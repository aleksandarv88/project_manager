from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Dev-only data reset: truncates all public tables and restarts identities (keeps schema/migrations)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Skip confirmation prompt.",
        )

    def handle(self, *args, **options):
        confirmed = bool(options.get("yes"))
        if not confirmed:
            answer = input(
                "This will DELETE ALL DATA from public schema tables (keeping schema/migration history). Continue? [y/N]: "
            ).strip().lower()
            if answer not in {"y", "yes"}:
                self.stdout.write(self.style.WARNING("Cancelled."))
                return

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                  AND tablename <> 'django_migrations'
                ORDER BY tablename;
                """
            )
            tables = [row[0] for row in cursor.fetchall()]

            if not tables:
                self.stdout.write("DONE")
                return

            quoted = ", ".join(connection.ops.quote_name(table) for table in tables)
            sql = f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE;"
            try:
                cursor.execute(sql)
            except Exception as exc:  # noqa: BLE001
                raise CommandError(f"Failed to reset DB: {exc}") from exc

        self.stdout.write("DONE")

