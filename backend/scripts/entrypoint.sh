#!/bin/sh
set -e

echo "Waiting for database..."
python -c "
import time, sys
from sqlalchemy import create_engine, text
import os

url = os.environ.get('DATABASE_URL', '')
for i in range(30):
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('Database is ready!')
        sys.exit(0)
    except Exception:
        print(f'Waiting... ({i+1}/30)')
        time.sleep(2)
print('Database connection failed!')
sys.exit(1)
"

echo "Initializing database..."
python -m scripts.init_db

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WORKERS:-2}
