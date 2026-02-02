'use client';

import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface StatsProps {
    stats: {
        total_products: number;
        total_units_sold: number;
        revenue_proxy: number;
        avg_price: number;
        avg_rating: number;
        avg_discount: number;
    } | null;
}

const formatIDR = (value: number) => {
    if (value >= 1000000000000) return (value / 1000000000000).toFixed(1) + ' T';
    if (value >= 1000000000) return (value / 1000000000).toFixed(1) + ' M';
    if (value >= 1000000) return (value / 1000000).toFixed(1) + ' Jt';
    if (value >= 1000) return (value / 1000).toFixed(0) + ' K';
    return Math.round(value).toLocaleString('id-ID');
};

export default function DashboardStats({ stats }: StatsProps) {
    if (!stats) return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4 mb-8">
            {[...Array(6)].map((_, i) => (
                <div key={i} className="card-terminal animate-pulse h-28 bg-[#141B2D]/50"></div>
            ))}
        </div>
    );

    return (
        <div className="grid grid-cols-12 gap-4 mb-8">
            <div className="col-span-12 sm:col-span-6 lg:col-span-2">
                <KPICard
                    label="Catalog Size"
                    value={stats.total_products.toLocaleString()}
                    subValue="Products Indexed"
                    color="text-[#E2E8F0]"
                />
            </div>
            <div className="col-span-12 sm:col-span-6 lg:col-span-2">
                <KPICard
                    label="Units Sold"
                    value={formatIDR(stats.total_units_sold)}
                    subValue="Market Volume"
                    color="text-[#10B981]"
                />
            </div>
            <div className="col-span-12 sm:col-span-6 lg:col-span-2">
                <KPICard
                    label="Est. Revenue"
                    value={`Rp ${formatIDR(stats.revenue_proxy)}`}
                    subValue="Financial Proxy"
                    color="text-[#3B82F6]"
                />
            </div>
            <div className="col-span-12 sm:col-span-6 lg:col-span-2">
                <KPICard
                    label="Avg Price"
                    value={`Rp ${formatIDR(stats.avg_price)}`}
                    subValue="Effective Market"
                    color="text-[#E2E8F0]"
                />
            </div>
            <div className="col-span-12 sm:col-span-6 lg:col-span-2">
                <KPICard
                    label="Avg Discount"
                    value={`${(stats.avg_discount * 100).toFixed(1)}%`}
                    subValue="Markdowns"
                    color="text-[#F59E0B]"
                />
            </div>
            <div className="col-span-12 sm:col-span-6 lg:col-span-2">
                <KPICard
                    label="Market Rating"
                    value={stats.avg_rating.toFixed(2)}
                    subValue="Average Score"
                    icon="★"
                    color="text-[#8B5CF6]"
                />
            </div>
        </div>
    );
}

function KPICard({ label, value, subValue, color, icon }: any) {
    return (
        <div className="card-terminal flex flex-col justify-between group h-28">
            <div className="flex justify-between items-start">
                <h3 className="text-[10px] font-display font-bold text-[#94A3B8] uppercase tracking-widest group-hover:text-[#3B82F6] transition-colors">
                    {label}
                </h3>
            </div>

            <div className="mt-2 flex items-baseline gap-1">
                <span className={`text-2xl font-mono font-bold tracking-tighter ${color} whitespace-nowrap`}>
                    {value}
                </span>
                {icon && <span className="text-sm opacity-30">{icon}</span>}
            </div>

            <div className="mt-1">
                <span className="text-[10px] font-body text-[#1E293B] font-bold uppercase tracking-tighter group-hover:text-[#94A3B8] transition-colors">
                    {subValue || "Total Aggregate"}
                </span>
            </div>
        </div>
    );
}
