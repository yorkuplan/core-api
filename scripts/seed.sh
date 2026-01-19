#!/bin/bash

# Seed script for populating the DB

set -e

echo "Seeding database..."

# Use DATABASE_URL from environment (provided by Render)
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL environment variable is not set"
    exit 1
fi

# Ensure SSL mode is set correctly (psql supports both postgres:// and postgresql://)
# Detect if it's Render (hostname starts with "dpg-") or docker-compose (hostname is "postgres")
SEED_URL="$DATABASE_URL"
if [[ "$SEED_URL" != *"sslmode"* ]]; then
    if [[ "$SEED_URL" == *"@dpg-"* ]]; then
        # Render databases require SSL
        if [[ "$SEED_URL" == *"?"* ]]; then
            SEED_URL="${SEED_URL}&sslmode=require"
        else
            SEED_URL="${SEED_URL}?sslmode=require"
        fi
    elif [[ "$SEED_URL" == *"@postgres:"* ]]; then
        # Docker-compose local database doesn't use SSL
        if [[ "$SEED_URL" == *"?"* ]]; then
            SEED_URL="${SEED_URL}&sslmode=disable"
        else
            SEED_URL="${SEED_URL}?sslmode=disable"
        fi
    fi
    # If neither pattern matches, don't add sslmode (use's default)
fi

# Run seed file using DATABASE_URL directly (psql supports connection strings)
if [ -f "./db/seed.sql" ]; then
    echo "Running seed file..."
    # psql can use DATABASE_URL directly
    psql "$SEED_URL" -f ./db/seed.sql
    echo "Database seeded successfully!"
else
    echo "Warning: seed.sql file not found. Skipping seeding."
fi

