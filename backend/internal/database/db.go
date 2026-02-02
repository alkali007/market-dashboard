package database

import (
	"context"
	"fmt"
	"os"

	"github.com/jackc/pgx/v4/pgxpool"
)

var Pool *pgxpool.Pool

func Connect() error {
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		return fmt.Errorf("DATABASE_URL is not set")
	}

	config, err := pgxpool.ParseConfig(dbURL)
	if err != nil {
		return fmt.Errorf("unable to parse database url: %v", err)
	}

	// Disable prepared statements for PGBouncer/Supavisor compatibility
	config.ConnConfig.PreferSimpleProtocol = true

	Pool, err = pgxpool.ConnectConfig(context.Background(), config)
	if err != nil {
		return fmt.Errorf("unable to connect to database: %v", err)
	}

	return nil
}

func Close() {
	if Pool != nil {
		Pool.Close()
	}
}
