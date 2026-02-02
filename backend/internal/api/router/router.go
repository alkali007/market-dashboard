package router

import (
	"market_dashboard/internal/api/handlers"
	auth "market_dashboard/internal/api/middleware"
	"net/http"
	"os"
	"strings"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

func CorsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		allowedOrigins := os.Getenv("ALLOWED_ORIGINS")
		origin := r.Header.Get("Origin")

		// If no allowed origins are set, default to * (dev mode)
		if allowedOrigins == "" {
			w.Header().Set("Access-Control-Allow-Origin", "*")
		} else {
			// Check if origin is in allowed list
			origins := strings.Split(allowedOrigins, ",")
			for _, o := range origins {
				if strings.TrimSpace(o) == origin {
					w.Header().Set("Access-Control-Allow-Origin", origin)
					break
				}
			}
		}

		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, X-API-Key")
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func NewRouter() *chi.Mux {
	r := chi.NewRouter()

	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(CorsMiddleware)

	// Rate Limiting (10 requests per second per IP roughly, or global depending on chi implementation)
	// We'll use a simple global throttle for simplicity in this project
	r.Use(middleware.Throttle(20)) // Allow 20 concurrent requests

	r.Get("/", handlers.RootHandler)
	r.Get("/health", handlers.HealthCheck)

	// Protected Analytics Endpoints
	r.Group(func(r chi.Router) {
		r.Use(auth.APIKeyAuth)

		r.Get("/products", handlers.GetProducts)
		r.Get("/dashboard/kpi", handlers.GetDetailedStats)
		r.Get("/dashboard/scatter", handlers.GetScatterData)
		r.Get("/dashboard/distribution", handlers.GetDistribution)
		r.Get("/dashboard/heatmap", handlers.GetHeatmapData)
		r.Get("/dashboard/brand", handlers.GetBrandPerformance)
		r.Get("/dashboard/product-type", handlers.GetProductTypePerformance)
	})

	return r
}
