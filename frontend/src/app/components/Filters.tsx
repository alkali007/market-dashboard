'use client';

import React, { useState } from 'react';
import { X, ChevronDown, ChevronRight, Filter } from 'lucide-react';

interface FilterProps {
    brands: { name: string; count: number }[];
    types: { name: string; count: number }[];
    selectedBrands: string[];
    selectedTypes: string[];
    selectedSources: string[];
    priceRange: [number, number];
    ratingRange: [number, number];
    discountRange: [number, number];
    onBrandChange: (brand: string) => void;
    onTypeChange: (type: string) => void;
    onSourceChange: (source: string) => void;
    onPriceChange: (min: number, max: number) => void;
    onRatingChange: (min: number, max: number) => void;
    onDiscountChange: (min: number, max: number) => void;
    onClearFilters: () => void;
}

export default function Filters({
    brands,
    types,
    selectedBrands,
    selectedTypes,
    selectedSources,
    priceRange,
    ratingRange,
    discountRange,
    onBrandChange,
    onTypeChange,
    onSourceChange,
    onPriceChange,
    onRatingChange,
    onDiscountChange,
    onClearFilters
}: FilterProps) {
    const [collapsed, setCollapsed] = useState<Record<string, boolean>>({
        sources: false,
        brands: false,
        types: false,
        ranges: false
    });

    const toggleCollapse = (key: string) => {
        setCollapsed(prev => ({ ...prev, [key]: !prev[key] }));
    };

    const activeCount = selectedBrands.length + selectedTypes.length +
        (priceRange[0] > 0 || priceRange[1] < 200000 ? 1 : 0) +
        (ratingRange[0] > 0 || ratingRange[1] < 5 ? 1 : 0) +
        (discountRange[0] > 0 || discountRange[1] < 100 ? 1 : 0);

    return (
        <div className="w-64 bg-[#141B2D] border-r border-[#1E293B] flex-shrink-0 flex flex-col h-screen sticky top-0 overflow-y-auto custom-scrollbar">
            <div className="p-6 border-b border-[#1E293B] flex justify-between items-center bg-[#141B2D] sticky top-0 z-10">
                <div className="flex items-center gap-2">
                    <Filter size={18} className="text-[#3B82F6]" />
                    <h2 className="text-sm font-display font-bold text-[#E2E8F0] uppercase tracking-widest">
                        Analysis Filters
                    </h2>
                </div>
                {activeCount > 0 && (
                    <button
                        onClick={onClearFilters}
                        className="text-[10px] font-bold text-[#EF4444] hover:text-[#EF4444]/80 uppercase tracking-tighter flex items-center gap-1 border border-[#EF4444]/20 px-2 py-1 rounded bg-[#EF4444]/5"
                    >
                        <X size={10} /> Clear ({activeCount})
                    </button>
                )}
            </div>

            <div className="p-4 space-y-2">
                <FilterGroup
                    title="Market Platforms"
                    count={selectedSources.length}
                    isCollapsed={collapsed.sources}
                    onToggle={() => toggleCollapse('sources')}
                >
                    <div className="space-y-1.5 mt-2">
                        {[
                            { id: 'tiktok', name: 'TikTok Shop' },
                            { id: 'shopee', name: 'Shopee' },
                            { id: 'tokopedia', name: 'Tokopedia' },
                            { id: 'lazada', name: 'Lazada' },
                            { id: 'blibli', name: 'Blibli' }
                        ].map((src) => (
                            <label key={src.id} className="flex items-center group cursor-pointer py-0.5">
                                <input
                                    type="checkbox"
                                    checked={selectedSources.includes(src.id)}
                                    onChange={() => onSourceChange(src.id)}
                                    className="appearance-none w-3.5 h-3.5 border border-[#1E293B] rounded bg-[#0B1120] checked:bg-[#10B981] checked:border-transparent transition-all mr-2 flex-shrink-0 cursor-pointer"
                                />
                                <span className={`text-xs text-[#94A3B8] group-hover:text-[#E2E8F0] transition-colors truncate flex-1 font-body`}>
                                    {src.name}
                                </span>
                            </label>
                        ))}
                    </div>
                </FilterGroup>

                <FilterGroup
                    title="Market Brands"
                    count={selectedBrands.length}
                    isCollapsed={collapsed.brands}
                    onToggle={() => toggleCollapse('brands')}
                >
                    <div className="space-y-1.5 max-h-96 overflow-y-auto pr-2 custom-scrollbar mt-2">
                        {brands.map((brand) => (
                            <label key={brand.name} className="flex items-center group cursor-pointer py-0.5">
                                <input
                                    type="checkbox"
                                    checked={selectedBrands.includes(brand.name)}
                                    onChange={() => onBrandChange(brand.name)}
                                    className="appearance-none w-3.5 h-3.5 border border-[#1E293B] rounded bg-[#0B1120] checked:bg-[#3B82F6] checked:border-transparent transition-all mr-2 flex-shrink-0 cursor-pointer"
                                />
                                <span className={`text-xs ${brand.count === 0 ? 'text-[#1E293B] line-through' : 'text-[#94A3B8]'} group-hover:text-[#E2E8F0] transition-colors truncate flex-1 font-body`}>
                                    {brand.name}
                                </span>
                                <span className={`text-[10px] font-mono font-bold ${brand.count === 0 ? 'text-[#1E293B]' : 'text-[#3B82F6]'} transition-colors`}>
                                    {brand.count}
                                </span>
                            </label>
                        ))}
                    </div>
                </FilterGroup>

                {/* Product Types Block */}
                <FilterGroup
                    title="Product Categories"
                    count={selectedTypes.length}
                    isCollapsed={collapsed.types}
                    onToggle={() => toggleCollapse('types')}
                >
                    <div className="space-y-1.5 max-h-96 overflow-y-auto pr-2 custom-scrollbar mt-2">
                        {types.map((type) => (
                            <label key={type.name} className="flex items-center group cursor-pointer py-0.5">
                                <input
                                    type="checkbox"
                                    checked={selectedTypes.includes(type.name)}
                                    onChange={() => onTypeChange(type.name)}
                                    className="appearance-none w-3.5 h-3.5 border border-[#1E293B] rounded bg-[#0B1120] checked:bg-[#8B5CF6] checked:border-transparent transition-all mr-2 flex-shrink-0 cursor-pointer"
                                />
                                <span className={`text-xs ${type.count === 0 ? 'text-[#1E293B] line-through' : 'text-[#94A3B8]'} group-hover:text-[#E2E8F0] transition-colors truncate flex-1 font-body`}>
                                    {type.name}
                                </span>
                                <span className={`text-[10px] font-mono font-bold ${type.count === 0 ? 'text-[#1E293B]' : 'text-[#8B5CF6]'} transition-colors`}>
                                    {type.count}
                                </span>
                            </label>
                        ))}
                    </div>
                </FilterGroup>

                {/* Range Sliders */}
                <FilterGroup
                    title="Performance Ranges"
                    isCollapsed={collapsed.ranges}
                    onToggle={() => toggleCollapse('ranges')}
                >
                    <div className="space-y-6 mt-4 pb-4">
                        <RangeSlider
                            label="Price (Rp)"
                            min={0}
                            max={200000}
                            step={5000}
                            value={priceRange}
                            onChange={onPriceChange}
                        />
                        <RangeSlider
                            label="Rating (★)"
                            min={0}
                            max={5}
                            step={0.1}
                            value={ratingRange}
                            onChange={onRatingChange}
                        />
                        <RangeSlider
                            label="Discount (%)"
                            min={0}
                            max={100}
                            step={1}
                            value={discountRange}
                            onChange={onDiscountChange}
                        />
                    </div>
                </FilterGroup>
            </div>
        </div>
    );
}

function FilterGroup({ title, count, children, isCollapsed, onToggle }: any) {
    return (
        <div className="border-b border-[#1E293B]/50 last:border-0 pb-2 mb-2">
            <button
                onClick={onToggle}
                className="w-full flex justify-between items-center py-2 group text-left"
            >
                <div className="flex items-center gap-2">
                    {isCollapsed ? <ChevronRight size={14} className="text-[#1E293B]" /> : <ChevronDown size={14} className="text-[#3B82F6]" />}
                    <span className="text-[11px] font-display font-bold text-[#94A3B8] uppercase tracking-widest group-hover:text-[#E2E8F0] transition-colors">
                        {title}
                        {count > 0 && <span className="ml-2 text-[#3B82F6]">({count})</span>}
                    </span>
                </div>
            </button>
            {!isCollapsed && (
                <div className="animate-in fade-in slide-in-from-top-1 duration-200">
                    {children}
                </div>
            )}
        </div>
    );
}

function RangeSlider({ label, min, max, step, value, onChange }: any) {
    return (
        <div className="px-1">
            <div className="flex justify-between items-center mb-2">
                <span className="text-[10px] font-bold text-[#E2E8F0] uppercase tracking-tighter opacity-70">
                    {label}
                </span>
                <span className="text-[10px] font-mono text-[#3B82F6]">
                    {value[0].toLocaleString()} - {value[1].toLocaleString()}
                </span>
            </div>
            <div className="relative h-1 bg-[#1E293B] rounded-full group cursor-pointer">
                {/* Simplified range slider implementation for now */}
                <input
                    type="range"
                    min={min}
                    max={max}
                    step={step}
                    value={value[0]}
                    onChange={(e) => onChange(Number(e.target.value), value[1])}
                    className="absolute w-full h-full appearance-none bg-transparent pointer-events-auto cursor-pointer z-10"
                />
                <input
                    type="range"
                    min={min}
                    max={max}
                    step={step}
                    value={value[1]}
                    onChange={(e) => onChange(value[0], Number(e.target.value))}
                    className="absolute w-full h-full appearance-none bg-transparent pointer-events-auto cursor-pointer z-20"
                />
                {/* Visual Track */}
                <div
                    className="absolute h-full bg-[#3B82F6] opacity-50 rounded-full"
                    style={{
                        left: `${((value[0] - min) / (max - min)) * 100}%`,
                        right: `${100 - ((value[1] - min) / (max - min)) * 100}%`
                    }}
                />
            </div>
        </div>
    );
}
