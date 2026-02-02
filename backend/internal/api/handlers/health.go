package handlers

import (
	"net/http"
)

func HealthCheck(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte("OK"))
}

func RootHandler(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte("Market Intelligence API is running"))
}
