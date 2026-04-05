from django.db import migrations, connection


def add_columns_if_missing(apps, schema_editor):
    """Add candidate_json and gpa_raw to the bot's `applications` table.

    This table is UNMANAGED (managed=False in BotApplication).
    It exists only in the remote Supabase PostgreSQL — NOT in local SQLite.
    So we skip entirely when running on SQLite (local dev).
    """
    db = schema_editor.connection.vendor  # 'sqlite' or 'postgresql'

    if db == 'sqlite':
        # Table doesn't exist locally — nothing to do
        return

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'applications'"
        )
        existing = {row[0] for row in cursor.fetchall()}

        if 'candidate_json' not in existing:
            cursor.execute('ALTER TABLE applications ADD COLUMN candidate_json JSONB')

        if 'gpa_raw' not in existing:
            cursor.execute('ALTER TABLE applications ADD COLUMN gpa_raw VARCHAR(50)')


def remove_columns(apps, schema_editor):
    db = schema_editor.connection.vendor
    if db == 'sqlite':
        return  # Nothing was done, nothing to undo
    with connection.cursor() as cursor:
        cursor.execute('ALTER TABLE applications DROP COLUMN IF EXISTS candidate_json')
        cursor.execute('ALTER TABLE applications DROP COLUMN IF EXISTS gpa_raw')


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0010_application_ent_score_application_ielts_score_and_more'),
    ]

    operations = [
        migrations.RunPython(add_columns_if_missing, reverse_code=remove_columns),
    ]
