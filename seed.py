import os
import sys

# Pastikan root backend ada di sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.seed.seed_data import seed_database

if __name__ == "__main__":
    print("=" * 65)
    print("  🔬 BRIN Research Table - Fresh Database Seeder")
    print("=" * 65)
    seed_database()
