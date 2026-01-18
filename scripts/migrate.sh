#!/bin/bash

# Runs DB migrations

set -e

echo "Running database migrations..."

# Use DATABASE_URL from environment (provided by Render)
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL environment variable is not set"
    exit 1
fi

# Normalize postgresql:// to postgres:// for golang-migrate
# Also ensure SSL mode is set for Render databases
MIGRATE_URL="$DATABASE_URL"
if [[ "$MIGRATE_URL" == postgresql://* ]]; then
    MIGRATE_URL="${MIGRATE_URL/postgresql:/postgres:}"
fi

# Add sslmode=require if not present (Render databases require SSL)
if [[ "$MIGRATE_URL" != *"sslmode"* ]]; then
    if [[ "$MIGRATE_URL" == *"?"* ]]; then
        MIGRATE_URL="${MIGRATE_URL}&sslmode=require"
    else
        MIGRATE_URL="${MIGRATE_URL}?sslmode=require"
    fi
fi

echo "Running migrations with connection string..."

# Run migrations
migrate -path ./migrations -database "$MIGRATE_URL" up

echo "Migrations completed successfully!"

