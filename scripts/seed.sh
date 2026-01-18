#!/bin/bash

# Seed script for populating the DB

set -e

echo "Seeding database..."

# Use DATABASE_URL from environment (provided by Render)
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL environment variable is not set"
    exit 1
fi

# Ensure SSL mode is set for Render databases (psql supports both postgres:// and postgresql://)
SEED_URL="$DATABASE_URL"
if [[ "$SEED_URL" != *"sslmode"* ]]; then
    if [[ "$SEED_URL" == *"?"* ]]; then
        SEED_URL="${SEED_URL}&sslmode=require"
    else
        SEED_URL="${SEED_URL}?sslmode=require"
    fi
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

