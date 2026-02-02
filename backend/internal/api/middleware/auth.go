package middleware

import (
	"net/http"
	"os"
)

// APIKeyAuth is a middleware that validates the X-API-Key header
func APIKeyAuth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		apiKey := os.Getenv("API_KEY")

		// If API_KEY is not set in environment, we allow access for development
		// BUT in production, this should always be set.
		if apiKey == "" {
			next.ServeHTTP(w, r)
			return
		}

		requestKey := r.Header.Get("X-API-Key")
		if requestKey == "" || requestKey != apiKey {
			http.Error(w, "Unauthorized: Invalid or missing API Key", http.StatusUnauthorized)
			return
		}

		next.ServeHTTP(w, r)
	})
}
