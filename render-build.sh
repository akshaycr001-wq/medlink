#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Database initialization
if [ ! -d "migrations" ]; then
    flask db init
fi
flask db migrate -m "Auto migration" || true
flask db upgrade
