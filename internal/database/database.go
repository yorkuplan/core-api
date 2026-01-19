package database

import (
	"context"
	"fmt"
	"strings"

	"github.com/jackc/pgx/v4/pgxpool"
)

func NewPool(ctx context.Context, databaseUrl string) (*pgxpool.Pool, error) {
	// Normalize postgresql:// to postgres:// for pgx
	normalizedUrl := databaseUrl
	if strings.HasPrefix(normalizedUrl, "postgresql://") {
		normalizedUrl = strings.Replace(normalizedUrl, "postgresql://", "postgres://", 1)
	}
	
	// Only add sslmode if not already present
	// Detect if it's Render (hostname starts with "dpg-") or docker-compose (hostname is "postgres")
	if !strings.Contains(normalizedUrl, "sslmode=") {
		// Check if it's a Render database (hostname pattern dpg-*)
		isRender := strings.Contains(normalizedUrl, "@dpg-")
		// Check if it's docker-compose (hostname is "postgres")
		isDockerCompose := strings.Contains(normalizedUrl, "@postgres:")
		
		if isRender {
			// Render databases require SSL
			if strings.Contains(normalizedUrl, "?") {
				normalizedUrl = normalizedUrl + "&sslmode=require"
			} else {
				normalizedUrl = normalizedUrl + "?sslmode=require"
			}
		} else if isDockerCompose {
			// Docker-compose local database doesn't use SSL
			if strings.Contains(normalizedUrl, "?") {
				normalizedUrl = normalizedUrl + "&sslmode=disable"
			} else {
				normalizedUrl = normalizedUrl + "?sslmode=disable"
			}
		}
		// If neither pattern matches, don't add sslmode (let it use default)
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
