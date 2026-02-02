package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"

	"market_dashboard/internal/database"
)

type DashboardKPI struct {
	TotalProducts  int     `json:"total_products"`
	TotalUnitsSold int64   `json:"total_units_sold"`
	RevenueProxy   float64 `json:"revenue_proxy"`
	AvgPrice       float64 `json:"avg_price"`
	AvgRating      float64 `json:"avg_rating"`
	AvgDiscount    float64 `json:"avg_discount"`
}

type HeatmapCell struct {
	Brand       string  `json:"brand"`
	ProductType string  `json:"product_type"`
	Value       float64 `json:"value"`
}

type BrandPerformance struct {
	Brand     string  `json:"brand"`
	UnitsSold int64   `json:"units_sold"`
	Revenue   float64 `json:"revenue"`
	AvgPrice  float64 `json:"avg_price"`
	AvgRating float64 `json:"avg_rating"`
	Count     int     `json:"count"`
}

type ScatterPoint struct {
	ID        string  `json:"id"`
	X         float64 `json:"x"`
	Y         float64 `json:"y"`
	Fill      string  `json:"fill"` // For categorization color
	Name      string  `json:"name"`
	Secondary float64 `json:"secondary,omitempty"` // e.g. Rating
}

type Item struct {
	Name  string `json:"name"`
	Count int    `json:"count"`
}

// buildWhereClause builds common filters for all handlers
func buildWhereClause(r *http.Request) (string, []interface{}) {
	query := " WHERE 1=1"
	var args []interface{}
	idx := 1

	// Categorical Multi-select
	brands := r.URL.Query()["brand"]
	if len(brands) > 0 {
		query += " AND brand = ANY($" + strconv.Itoa(idx) + ")"
		args = append(args, brands)
		idx++
	}

	types := r.URL.Query()["product_type"]
	if len(types) > 0 {
		query += " AND product_type = ANY($" + strconv.Itoa(idx) + ")"
		args = append(args, types)
		idx++
	}

	// Range Filters
	ranges := []struct {
		param string
		col   string
	}{
		{"min_price", "price_effective >= "},
		{"max_price", "price_effective <= "},
		{"min_rating", "rating >= "},
		{"max_rating", "rating <= "},
		{"min_discount", "discount >= "},
		{"max_discount", "discount <= "},
	}

	for _, rg := range ranges {
		val := r.URL.Query().Get(rg.param)
		if val != "" {
			if f, err := strconv.ParseFloat(val, 64); err == nil {
				// For discount, if user enters > 1 (e.g. 10 for 10%), convert to 0-1
				if (rg.param == "min_discount" || rg.param == "max_discount") && f > 1.0 {
					f = f / 100.0
				}
				query += " AND " + rg.col + "$" + strconv.Itoa(idx)
				args = append(args, f)
				idx++
			}
		}
	}

	return query, args
}

// GetDetailedStats returns the high-level KPIs based on filters
func GetDetailedStats(w http.ResponseWriter, r *http.Request) {
	stats := DashboardKPI{}
	ctx := context.Background()

	whereClause, args := buildWhereClause(r)

	query := `
		SELECT 
			COUNT(*), 
			COALESCE(SUM(quantity_sold), 0), 
			COALESCE(SUM(revenue_proxy), 0),
			COALESCE(SUM(revenue_proxy) / NULLIF(SUM(quantity_sold), 0), 0) as weighted_avg_price,
			COALESCE(AVG(rating), 0),
			COALESCE(SUM(discount * quantity_sold) / NULLIF(SUM(quantity_sold), 0), 0) as weighted_avg_discount
		FROM analytics_master
	` + whereClause

	err := database.Pool.QueryRow(ctx, query, args...).Scan(
		&stats.TotalProducts,
		&stats.TotalUnitsSold,
		&stats.RevenueProxy,
		&stats.AvgPrice,
		&stats.AvgRating,
		&stats.AvgDiscount,
	)

	if err != nil {
		fmt.Printf("Error fetching KPIs: %v\n", err)
		http.Error(w, "Error fetching KPIs: "+err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stats)
}

func GetScatterData(w http.ResponseWriter, r *http.Request) {
	chartType := r.URL.Query().Get("type")
	whereClause, args := buildWhereClause(r)

	ctx := context.Background()
	var query string
	var points []ScatterPoint

	if chartType == "discount_rating" {
		query = `
			SELECT id, discount, rating, brand 
			FROM analytics_master 
		` + whereClause + ` AND rating IS NOT NULL AND discount IS NOT NULL LIMIT 2000`

		rows, err := database.Pool.Query(ctx, query, args...)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		defer rows.Close()

		brands := make(map[string]int)
		palette := []string{"#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899"}

		for rows.Next() {
			var p ScatterPoint
			var brand string
			if err := rows.Scan(&p.ID, &p.X, &p.Y, &brand); err != nil {
				continue
			}
			p.X = p.X * 100 // Convert to percentage
			p.Name = brand
			if _, ok := brands[brand]; !ok {
				brands[brand] = len(brands) % len(palette)
			}
			p.Fill = palette[brands[brand]]
			points = append(points, p)
		}
	} else {
		// Default: price_quantity
		query = `
			SELECT id, price_effective, quantity_sold, product_type 
			FROM analytics_master 
		` + whereClause + ` AND price_effective IS NOT NULL AND quantity_sold IS NOT NULL LIMIT 2000`

		rows, err := database.Pool.Query(ctx, query, args...)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		defer rows.Close()

		types := make(map[string]int)
		palette := []string{"#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899"}

		for rows.Next() {
			var p ScatterPoint
			var pType string
			if err := rows.Scan(&p.ID, &p.X, &p.Y, &pType); err != nil {
				continue
			}
			p.Name = pType
			if _, ok := types[pType]; !ok {
				types[pType] = len(types) % len(palette)
			}
			p.Fill = palette[types[pType]]
			points = append(points, p)
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(points)
}

func GetDistribution(w http.ResponseWriter, r *http.Request) {
	distType := r.URL.Query().Get("type")
	limitStr := r.URL.Query().Get("limit")
	limit := 100
	if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
		limit = l
	}

	whereClause, args := buildWhereClause(r)
	ctx := context.Background()
	var query string

	// Note: We need to inject whereClause before GROUP BY
	// Simple append won't work if query structure changes

	if distType == "category" {
		query = `
			SELECT product_type, COUNT(*) as count 
			FROM analytics_master 
			` + whereClause + `
			GROUP BY product_type 
			ORDER BY count DESC 
			LIMIT ` + strconv.Itoa(limit)
	} else {
		query = `
			SELECT brand, COUNT(*) as count 
			FROM analytics_master 
			` + whereClause + `
			GROUP BY brand 
			ORDER BY count DESC 
			LIMIT ` + strconv.Itoa(limit)
	}

	rows, err := database.Pool.Query(ctx, query, args...)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var items []Item
	for rows.Next() {
		var i Item
		if err := rows.Scan(&i.Name, &i.Count); err != nil {
			continue
		}
		items = append(items, i)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(items)
}

func GetHeatmapData(w http.ResponseWriter, r *http.Request) {
	metric := r.URL.Query().Get("metric") // "units" or "rating"
	whereClause, args := buildWhereClause(r)
	ctx := context.Background()

	valCol := "COALESCE(SUM(quantity_sold), 0)"
	if metric == "rating" {
		valCol = "COALESCE(AVG(rating), 0)"
	}

	query := fmt.Sprintf(`
		SELECT brand, product_type, %s
		FROM analytics_master
		%s
		GROUP BY brand, product_type
		HAVING %s > 0
		ORDER BY brand, product_type`, valCol, whereClause, valCol)

	rows, err := database.Pool.Query(ctx, query, args...)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var cells []HeatmapCell
	for rows.Next() {
		var c HeatmapCell
		if err := rows.Scan(&c.Brand, &c.ProductType, &c.Value); err != nil {
			continue
		}
		cells = append(cells, c)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(cells)
}

func GetBrandPerformance(w http.ResponseWriter, r *http.Request) {
	whereClause, args := buildWhereClause(r)
	ctx := context.Background()

	query := `
		SELECT 
			brand, 
			COALESCE(SUM(quantity_sold), 0) as units, 
			COALESCE(SUM(revenue_proxy), 0)::DOUBLE PRECISION as rev,
			COALESCE(AVG(price_effective), 0)::DOUBLE PRECISION as price,
			COALESCE(AVG(rating), 0)::DOUBLE PRECISION as rating,
			COUNT(*) as count
		FROM analytics_master
		` + whereClause + `
		GROUP BY brand
		ORDER BY rev DESC
		LIMIT 100`

	rows, err := database.Pool.Query(ctx, query, args...)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var results []BrandPerformance
	for rows.Next() {
		var bp BrandPerformance
		if err := rows.Scan(&bp.Brand, &bp.UnitsSold, &bp.Revenue, &bp.AvgPrice, &bp.AvgRating, &bp.Count); err != nil {
			continue
		}
		results = append(results, bp)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(results)
}

type ProductTypePerformance struct {
	ProductType string  `json:"product_type"`
	UnitsSold   int64   `json:"units_sold"`
	Revenue     float64 `json:"revenue"`
	AvgPrice    float64 `json:"avg_price"`
	Count       int     `json:"count"`
}

func GetProductTypePerformance(w http.ResponseWriter, r *http.Request) {
	whereClause, args := buildWhereClause(r)
	ctx := context.Background()

	query := `
		SELECT 
			product_type, 
			COALESCE(SUM(quantity_sold), 0) as units, 
			COALESCE(SUM(revenue_proxy), 0)::DOUBLE PRECISION as rev,
			COALESCE(AVG(price_effective), 0)::DOUBLE PRECISION as price,
			COUNT(*) as count
		FROM analytics_master
		` + whereClause + `
		GROUP BY product_type
		ORDER BY rev DESC
		LIMIT 100`

	rows, err := database.Pool.Query(ctx, query, args...)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var results []ProductTypePerformance
	for rows.Next() {
		var ptp ProductTypePerformance
		if err := rows.Scan(&ptp.ProductType, &ptp.UnitsSold, &ptp.Revenue, &ptp.AvgPrice, &ptp.Count); err != nil {
			continue
		}
		results = append(results, ptp)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(results)
}
