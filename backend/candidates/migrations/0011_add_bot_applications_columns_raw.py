from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0010_application_ent_score_application_ielts_score_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                -- Add candidate_json if it doesn't exist
                BEGIN
                    ALTER TABLE applications ADD COLUMN candidate_json JSONB;
                EXCEPTION
                    WHEN duplicate_column THEN RAISE NOTICE 'column candidate_json already exists in applications.';
                END;

                -- Add gpa_raw if it doesn't exist
                BEGIN
                    ALTER TABLE applications ADD COLUMN gpa_raw VARCHAR(50);
                EXCEPTION
                    WHEN duplicate_column THEN RAISE NOTICE 'column gpa_raw already exists in applications.';
                END;
            END $$;
            """,
            reverse_sql="""
            ALTER TABLE applications DROP COLUMN IF EXISTS candidate_json;
            ALTER TABLE applications DROP COLUMN IF EXISTS gpa_raw;
            """
        )
    ]
