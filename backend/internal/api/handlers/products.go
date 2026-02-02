package handlers

import (
	"context"
	"encoding/json"
	"net/http"

	"market_dashboard/internal/database"
	"market_dashboard/internal/models"
)

func GetProducts(w http.ResponseWriter, r *http.Request) {
	ctx := context.Background()
	whereClause, args := buildWhereClause(r)
	query := `
		SELECT 
			id, title_raw, brand, product_type, price_effective, rating
		FROM analytics_master
	` + whereClause + " LIMIT 100"

	rows, err := database.Pool.Query(ctx, query, args...)
	if err != nil {
		http.Error(w, "Failed to fetch products: "+err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var products []models.Product
	for rows.Next() {
		var p models.Product
		var rating *float64 // Handle nullable rating
		err := rows.Scan(
			&p.ID, &p.TitleRaw, &p.Brand, &p.ProductType,
			&p.PriceEffective, &rating,
		)
		if err != nil {
			http.Error(w, "Error scanning product: "+err.Error(), http.StatusInternalServerError)
			return
		}
		if rating != nil {
			p.Rating = *rating
		}
		products = append(products, p)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(products)
}
