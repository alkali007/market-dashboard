package models

import (
	"time"
)

type Product struct {
	ID             string    `json:"id"`
	TitleRaw       string    `json:"title_raw"`
	Brand          string    `json:"brand"`
    ProductType    string    `json:"product_type"`
    PriceEffective float64   `json:"price_effective"`
    Rating         float64   `json:"rating"`
    EnrichedAt     time.Time `json:"enriched_at"`
}

type AggregatedMetric struct {
    DimensionType    string  `json:"dimension_type"`
    DimensionBrand   *string `json:"dimension_brand,omitempty"`
    DimensionProduct *string `json:"dimension_product,omitempty"`
    TotalUnitsSold   int64   `json:"total_units_sold"`
    AvgPrice         float64 `json:"avg_price"`
    AvgRating        float64 `json:"avg_rating"`
}
