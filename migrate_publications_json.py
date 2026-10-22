"""
Migration script: Convert brin_author, research_center, and field columns in publications table to JSON.
Usage: python migrate_publications_json.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sqlalchemy import create_engine, text
from app.core.config import settings


def run_migration():
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    with engine.connect() as conn:
        print(f"Connecting to database: {settings.SQLALCHEMY_DATABASE_URI.split('@')[-1]}")
        print("Migrating publications columns to JSON...")

        # 1. brin_author
        try:
            conn.execute(text("""
                ALTER TABLE publications 
                ALTER COLUMN brin_author TYPE json USING 
                CASE 
                    WHEN brin_author IS NULL THEN '[]'::json
                    WHEN trim(brin_author) = '' THEN '[]'::json
                    WHEN trim(brin_author) LIKE '[%' THEN brin_author::json
                    ELSE to_json(string_to_array(brin_author, ';'))
                END;
            """))
            print("✓ Successfully migrated 'brin_author' to JSON")
        except Exception as e:
            print("! brin_author migration:", e)

        # 2. research_center
        try:
            conn.execute(text("""
                ALTER TABLE publications 
                ALTER COLUMN research_center TYPE json USING 
                CASE 
                    WHEN research_center IS NULL THEN '[]'::json
                    WHEN trim(research_center) = '' THEN '[]'::json
                    WHEN trim(research_center) LIKE '[%' THEN research_center::json
                    ELSE to_json(string_to_array(research_center, ';'))
                END;
            """))
            print("✓ Successfully migrated 'research_center' to JSON")
        except Exception as e:
            print("! research_center migration:", e)

        # 3. field
        try:
            conn.execute(text("""
                ALTER TABLE publications 
                ALTER COLUMN field TYPE json USING 
                CASE 
                    WHEN field IS NULL THEN '[]'::json
                    WHEN trim(field) = '' THEN '[]'::json
                    WHEN trim(field) LIKE '[%' THEN field::json
                    ELSE to_json(string_to_array(field, ';'))
                END;
            """))
            print("✓ Successfully migrated 'field' to JSON")
        except Exception as e:
            print("! field migration:", e)

        conn.commit()
        print("Migration complete!")


if __name__ == "__main__":
    run_migration()
