package router

import (
	"market_dashboard/internal/api/handlers"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

func CorsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
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

	r.Get("/", handlers.RootHandler)
	r.Get("/health", handlers.HealthCheck)
	r.Get("/products", handlers.GetProducts)

	// New Analytics Endpoints
	r.Get("/dashboard/kpi", handlers.GetDetailedStats)
	r.Get("/dashboard/scatter", handlers.GetScatterData)
	r.Get("/dashboard/distribution", handlers.GetDistribution)
	r.Get("/dashboard/heatmap", handlers.GetHeatmapData)
	r.Get("/dashboard/brand", handlers.GetBrandPerformance)
	r.Get("/dashboard/product-type", handlers.GetProductTypePerformance)

	return r
}
