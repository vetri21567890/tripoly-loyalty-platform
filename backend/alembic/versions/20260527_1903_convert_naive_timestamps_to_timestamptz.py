"""Convert naive timestamp columns to timestamptz.

Revision ID: 20260527_1903
Revises:
Create Date: 2026-05-27 19:03:00
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260527_1903"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        DECLARE
            row_record RECORD;
        BEGIN
            FOR row_record IN
                SELECT
                    n.nspname AS schema_name,
                    c.relname AS table_name,
                    a.attname AS column_name
                FROM pg_attribute a
                JOIN pg_class c ON c.oid = a.attrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                JOIN pg_type t ON t.oid = a.atttypid
                WHERE c.relkind = 'r'
                  AND n.nspname = 'public'
                  AND a.attnum > 0
                  AND NOT a.attisdropped
                  AND t.typname = 'timestamp'
            LOOP
                EXECUTE format(
                    'ALTER TABLE %I.%I ALTER COLUMN %I TYPE timestamptz USING %I AT TIME ZONE ''UTC''',
                    row_record.schema_name,
                    row_record.table_name,
                    row_record.column_name,
                    row_record.column_name
                );
            END LOOP;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        DECLARE
            row_record RECORD;
        BEGIN
            FOR row_record IN
                SELECT
                    n.nspname AS schema_name,
                    c.relname AS table_name,
                    a.attname AS column_name
                FROM pg_attribute a
                JOIN pg_class c ON c.oid = a.attrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                JOIN pg_type t ON t.oid = a.atttypid
                WHERE c.relkind = 'r'
                  AND n.nspname = 'public'
                  AND a.attnum > 0
                  AND NOT a.attisdropped
                  AND t.typname = 'timestamptz'
            LOOP
                EXECUTE format(
                    'ALTER TABLE %I.%I ALTER COLUMN %I TYPE timestamp USING %I AT TIME ZONE ''UTC''',
                    row_record.schema_name,
                    row_record.table_name,
                    row_record.column_name,
                    row_record.column_name
                );
            END LOOP;
        END $$;
        """
    )
