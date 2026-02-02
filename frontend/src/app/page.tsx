'use client';

import { useState, useEffect } from 'react';
import Filters from './components/Filters';
import DashboardStats from './components/DashboardStats';
import {
  BrandBySales,
  ProductByPrice,
  CategoryDonut,
  MarketHeatmap
} from './components/ComplexCharts';
import { RefreshCw, LayoutGrid } from 'lucide-react';

export default function Home() {
  const [data, setData] = useState<any>({
    kpi: null,
    priceScatter: [],
    distribution: [],
    brands: [],
    types: [],
    brandPerf: [],
    typePerf: [],
    heatmap: []
  });

  const [filters, setFilters] = useState({
    brand: [] as string[],
    product_type: [] as string[],
    min_price: 0,
    max_price: 200000,
    min_rating: 0,
    max_rating: 5,
    min_discount: 0,
    max_discount: 100
  });

  const [loading, setLoading] = useState(true);
  const [isMounted, setIsMounted] = useState(false);
  const [showNotify, setShowNotify] = useState(false);

  useEffect(() => {
    setIsMounted(true);
    fetchInitialData();
  }, []);

  // Debounced effect for filters
  useEffect(() => {
    if (!isMounted) return;

    const handler = setTimeout(() => {
      fetchData();
    }, 400);

    return () => clearTimeout(handler);
  }, [filters, isMounted]);

  const fetchInitialData = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8081';
      const apiKey = process.env.NEXT_PUBLIC_API_KEY || '';
      const [bRes, tRes] = await Promise.all([
        fetch(`${apiUrl}/dashboard/distribution?type=brand&limit=200`, {
          headers: { 'X-API-Key': apiKey }
        }),
        fetch(`${apiUrl}/dashboard/distribution?type=category&limit=100`, {
          headers: { 'X-API-Key': apiKey }
        })
      ]);
      const brands = await bRes.json();
      const types = await tRes.json();
      setData((prev: any) => ({ ...prev, brands, types }));
    } catch (e) {
      console.error(e);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const queryParams = new URLSearchParams();
      filters.brand.forEach(b => queryParams.append('brand', b));
      filters.product_type.forEach(t => queryParams.append('product_type', t));
      if (filters.min_price > 0) queryParams.append('min_price', filters.min_price.toString());
      if (filters.max_price < 200000) queryParams.append('max_price', filters.max_price.toString());
      if (filters.min_rating > 0) queryParams.append('min_rating', filters.min_rating.toString());
      if (filters.max_rating < 5) queryParams.append('max_rating', filters.max_rating.toString());
      if (filters.min_discount > 0) queryParams.append('min_discount', filters.min_discount.toString());
      if (filters.max_discount < 100) queryParams.append('max_discount', filters.max_discount.toString());

      const qs = queryParams.toString();

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8081';
      const apiKey = process.env.NEXT_PUBLIC_API_KEY || '';

      const headers = { 'X-API-Key': apiKey };

      const [kpi, ps, dist, bp, tp, hm] = await Promise.all([
        fetch(`${apiUrl}/dashboard/kpi?${qs}`, { headers }).then(r => r.json()),
        fetch(`${apiUrl}/dashboard/scatter?type=price_quantity&${qs}`, { headers }).then(r => r.json()),
        fetch(`${apiUrl}/dashboard/distribution?type=brand&${qs}`, { headers }).then(r => r.json()),
        fetch(`${apiUrl}/dashboard/brand?${qs}`, { headers }).then(r => r.json()),
        fetch(`${apiUrl}/dashboard/product-type?${qs}`, { headers }).then(r => r.json()),
        fetch(`${apiUrl}/dashboard/heatmap?${qs}`, { headers }).then(r => r.json())
      ]);


      if (kpi.total_products === 0) {
        setShowNotify(true);
        setTimeout(() => setShowNotify(false), 3000);
      }

      setData((prev: any) => ({
        ...prev,
        kpi,
        priceScatter: ps,
        distribution: dist,
        brandPerf: bp,
        typePerf: tp,
        heatmap: hm
      }));

      // NOTE: We intentionally DO NOT update brands/types here
      // This keeps all filter options visible regardless of selection

    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };


  const handleClearFilters = () => {
    setFilters({
      brand: [],
      product_type: [],
      min_price: 0,
      max_price: 200000,
      min_rating: 0,
      max_rating: 5,
      min_discount: 0,
      max_discount: 100
    });
  };

  if (!isMounted) return null;

  return (
    <div className="flex bg-[#0B1120] min-h-screen text-[#E2E8F0] relative overflow-hidden">
      {/* Toast Notification */}
      {showNotify && (
        <div className="fixed top-8 left-1/2 -translate-x-1/2 z-50 animate-in slide-in-from-top duration-300">
          <div className="bg-[#EF4444] text-white px-6 py-3 rounded-full shadow-2xl flex items-center gap-3 border border-white/20">
            <span className="text-sm font-bold uppercase tracking-wider">No Results Found</span>
            <div className="h-4 w-[1px] bg-white/30" />
            <span className="text-xs opacity-90">Adjust your filters to see data</span>
          </div>
        </div>
      )}

      {/* Left Sidebar */}
      <Filters
        brands={data.brands || []}
        types={data.types || []}
        selectedBrands={filters.brand}
        selectedTypes={filters.product_type}
        priceRange={[filters.min_price, filters.max_price]}
        ratingRange={[filters.min_rating, filters.max_rating]}
        discountRange={[filters.min_discount, filters.max_discount]}
        onBrandChange={(b: string) => setFilters((f: any) => ({
          ...f, brand: f.brand.includes(b) ? f.brand.filter((x: string) => x !== b) : [...f.brand, b]
        }))}
        onTypeChange={(t: string) => setFilters((f: any) => ({
          ...f, product_type: f.product_type.includes(t) ? f.product_type.filter((x: string) => x !== t) : [...f.product_type, t]
        }))}
        onPriceChange={(min: number, max: number) => setFilters((f: any) => ({ ...f, min_price: min, max_price: max }))}
        onRatingChange={(min: number, max: number) => setFilters((f: any) => ({ ...f, min_rating: min, max_rating: max }))}
        onDiscountChange={(min: number, max: number) => setFilters((f: any) => ({ ...f, min_discount: min, max_discount: max }))}
        onClearFilters={handleClearFilters}
      />

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto custom-scrollbar">
        <header className="p-8 pb-0 flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-display font-medium text-white tracking-tight">
              Personal Care Analytical Console
            </h1>
            <p className="text-[#94A3B8] text-xs mt-1 uppercase tracking-widest font-bold">
              Market Intelligence for Personal Care (Data Source: Tiktokshop)
            </p>
          </div>
          <button
            onClick={fetchData}
            className="flex items-center gap-2 px-4 py-2 bg-[#3B82F6] text-white rounded text-xs font-bold uppercase tracking-wider hover:bg-[#3B82F6]/80 transition-all shadow-[0_0_15px_-5px_#3B82F6]"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Sync Data
          </button>
        </header>

        <div className="p-8">
          {/* Stats Bar */}
          <DashboardStats stats={data.kpi} />

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-8">
            {/* Brand Performance */}
            <div className="lg:col-span-12 xl:col-span-4">
              <BrandBySales data={data.brandPerf || []} />
            </div>

            {/* Category Share */}
            <div className="lg:col-span-12 xl:col-span-4">
              <CategoryDonut data={data.distribution || []} />
            </div>

            {/* Product Type Performance */}
            <div className="lg:col-span-12 xl:col-span-4">
              <ProductByPrice data={data.typePerf || []} />
            </div>

            {/* Heatmap Section */}
            <div className="col-span-full">
              <MarketHeatmap data={data.heatmap || []} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
