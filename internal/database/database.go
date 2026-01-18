package database

import (
	"context"
	"fmt"
	"strings"

	"github.com/jackc/pgx/v4/pgxpool"
)

func NewPool(ctx context.Context, databaseUrl string) (*pgxpool.Pool, error) {
	// Ensure SSL mode is set for Render databases (they require SSL)
	// Normalize postgresql:// to postgres:// for pgx
	normalizedUrl := databaseUrl
	if strings.HasPrefix(normalizedUrl, "postgresql://") {
		normalizedUrl = strings.Replace(normalizedUrl, "postgresql://", "postgres://", 1)
	}
	
	// Add sslmode=require if not present (Render databases require SSL)
	if !strings.Contains(normalizedUrl, "sslmode=") {
		if strings.Contains(normalizedUrl, "?") {
			normalizedUrl = normalizedUrl + "&sslmode=require"
		} else {
			normalizedUrl = normalizedUrl + "?sslmode=require"
		}
	}

	config, err := pgxpool.ParseConfig(normalizedUrl)
	if err != nil {
		return nil, fmt.Errorf("Unable to parse the database url: %w", err)
	}

	pool, err := pgxpool.ConnectConfig(ctx, config)
	if err != nil {
		return nil, fmt.Errorf("Unable to create connection pool: %w", err)
	}

	if err := pool.Ping(ctx); err != nil {
		return nil, fmt.Errorf("Unable to ping database: %w", err)
	}

	return pool, nil
}
