#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Database initialization (Uncomment if you want to automate the first-time setup)
# if [ ! -d "migrations" ]; then
#     flask db init
#     flask db migrate -m "Initial migration"
#     flask db upgrade
# fi
