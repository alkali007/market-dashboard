package main

import (
	"log"
	"net/http"

	"market_dashboard/internal/api/router"
	"market_dashboard/internal/config"
	"market_dashboard/internal/database"
)

func main() {
	// Load Configuration
	cfg := config.LoadConfig()

	// Connect to Database
	if err := database.Connect(); err != nil {
		log.Fatalf("Could not connect to database: %v", err)
	}
	defer database.Close()
	log.Println("Connected to Database")

	// Initialize Router
	r := router.NewRouter()

	log.Printf("Server starting on port %s", cfg.Port)
	if err := http.ListenAndServe(":"+cfg.Port, r); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}
