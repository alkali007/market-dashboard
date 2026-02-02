'use client';

import React, { useEffect, useState } from 'react';
import {
    Tooltip,
    ResponsiveContainer,
    Cell,
    PieChart,
    Pie,
    Legend
} from 'recharts';


const CHART_PALETTE = [
    '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6',
    '#EC4899', '#14B8A6', '#F97316', '#6366F1'
];

interface ChartWrapperProps {
    title: string;
    iconColor: string;
    children: React.ReactNode;
    fullWidth?: boolean;
}

const ChartWrapper = ({ title, iconColor, children, fullWidth }: ChartWrapperProps) => (
    <div className={`card-terminal flex flex-col ${fullWidth ? 'col-span-full' : ''} h-[480px]`}>
        <div className="flex items-center justify-between mb-4 flex-shrink-0">
            <h3 className="text-sm font-display font-bold text-[#E2E8F0] uppercase tracking-widest flex items-center gap-2">
                <span className={`w-1.5 h-1.5 rounded-full ${iconColor}`}></span>
                {title}
            </h3>
            <div className="flex gap-1">
                <div className="w-1 h-1 bg-[#1E293B] rounded-full"></div>
                <div className="w-1 h-1 bg-[#1E293B] rounded-full"></div>
                <div className="w-1 h-1 bg-[#1E293B] rounded-full"></div>
            </div>
        </div>
        <div className="flex-1 w-full min-h-0 relative">
            {children}
        </div>
    </div>
);

const CustomTooltip = ({ active, payload, unit = '' }: any) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-[#0B1120] border border-[#1E293B] p-3 rounded shadow-2xl backdrop-blur-md z-50">
                <p className="text-[10px] font-mono text-[#94A3B8] mb-1 uppercase tracking-tighter">
                    {payload[0].payload.name || payload[0].name}
                </p>
                <div className="space-y-1">
                    {payload.map((item: any, i: number) => (
                        <div key={i} className="flex justify-between gap-4 items-center">
                            <span className="text-[10px] text-[#E2E8F0] font-bold uppercase">{item.name}:</span>
                            <span className="text-[11px] font-mono font-bold text-white">
                                {typeof item.value === 'number' ? item.value.toLocaleString() : item.value}{unit}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        );
    }
    return null;
};

const formatValueShort = (val: number) => {
    if (val >= 1000000000000) return `Rp ${(val / 1000000000000).toFixed(1)} T`;
    if (val >= 1000000000) return `Rp ${(val / 1000000000).toFixed(1)} M`;
    if (val >= 1000000) return `Rp ${(val / 1000000).toFixed(1)} Jt`;
    if (val >= 1000) return `Rp ${(val / 1000).toFixed(0)} K`;
    return `Rp ${Math.round(val).toLocaleString('id-ID')}`;
};

const formatUnits = (val: number) => {
    if (val >= 1000000) return `${(val / 1000000).toFixed(1)} Jt`;
    if (val >= 1000) return `${(val / 1000).toFixed(0)} K`;
    return Math.round(val).toLocaleString('id-ID');
};

// Product Type Performance Table
export function ProductByPrice({ data }: { data: any[] }) {
    const [mounted, setMounted] = useState(false);
    useEffect(() => { setMounted(true); }, []);
    if (!mounted) return <div className="card-terminal animate-pulse h-[480px]" />;

    const sorted = [...data].sort((a, b) => (b.revenue || 0) - (a.revenue || 0));

    return (
        <ChartWrapper title="Product Type Performance" iconColor="bg-[#8B5CF6]">
            <div className="absolute inset-0 overflow-y-auto pr-2 custom-scrollbar">
                <table className="w-full text-left border-collapse">
                    <thead className="sticky top-0 bg-[#0B1120] z-20 shadow-sm shadow-[#1E293B]">
                        <tr className="text-[9px] font-mono text-[#94A3B8] uppercase tracking-wider">
                            <th className="py-2 px-1">#</th>
                            <th className="py-2 px-1">Category</th>
                            <th className="py-2 px-1 text-right">Units</th>
                            <th className="py-2 px-1 text-right">Revenue</th>
                            <th className="py-2 px-1 text-right whitespace-nowrap">Avg Price</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-[#1E293B]">
                        {sorted.map((item, i) => (
                            <tr key={i} className={`hover:bg-[#1E293B]/50 transition-colors text-[11px] ${i >= 10 ? 'opacity-40 hover:opacity-100' : ''}`}>
                                <td className="py-2 px-1 font-mono text-[#8B5CF6]">{i + 1}</td>
                                <td className="py-2 px-1 text-[#E2E8F0] capitalize font-medium truncate max-w-[80px]" title={item.product_type}>
                                    {item.product_type}
                                </td>
                                <td className="py-2 px-1 text-right font-mono text-[#EC4899]">{formatUnits(item.units_sold || 0)}</td>
                                <td className="py-2 px-1 text-right font-mono text-[#10B981] font-bold">{formatValueShort(item.revenue || 0)}</td>
                                <td className="py-2 px-1 text-right font-mono text-[#F59E0B]">{formatValueShort(item.avg_price || 0)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </ChartWrapper>
    );
}


// Brand Performance Table
export function BrandBySales({ data }: { data: any[] }) {
    const [mounted, setMounted] = useState(false);
    useEffect(() => { setMounted(true); }, []);
    if (!mounted) return <div className="card-terminal animate-pulse h-[480px]" />;

    const sorted = [...data].sort((a, b) => (b.revenue || 0) - (a.revenue || 0));

    return (
        <ChartWrapper title="Brand Performance" iconColor="bg-[#3B82F6]">
            <div className="absolute inset-0 overflow-y-auto pr-2 custom-scrollbar">
                <table className="w-full text-left border-collapse">
                    <thead className="sticky top-0 bg-[#0B1120] z-20 shadow-sm shadow-[#1E293B]">
                        <tr className="text-[9px] font-mono text-[#94A3B8] uppercase tracking-wider">
                            <th className="py-2 px-1">#</th>
                            <th className="py-2 px-1">Brand</th>
                            <th className="py-2 px-1 text-right">Units</th>
                            <th className="py-2 px-1 text-right">Revenue</th>
                            <th className="py-2 px-1 text-right whitespace-nowrap">Avg Price</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-[#1E293B]">
                        {sorted.map((item, i) => (
                            <tr key={i} className={`hover:bg-[#1E293B]/50 transition-colors text-[11px] ${i >= 10 ? 'opacity-40 hover:opacity-100' : ''}`}>
                                <td className="py-2 px-1 font-mono text-[#3B82F6]">{i + 1}</td>
                                <td className="py-2 px-1 text-[#E2E8F0] capitalize font-medium truncate max-w-[80px]" title={item.brand}>
                                    {item.brand}
                                </td>
                                <td className="py-2 px-1 text-right font-mono text-[#EC4899]">{formatUnits(item.units_sold || 0)}</td>
                                <td className="py-2 px-1 text-right font-mono text-[#10B981] font-bold">{formatValueShort(item.revenue || 0)}</td>
                                <td className="py-2 px-1 text-right font-mono text-[#F59E0B]">{formatValueShort(item.avg_price || 0)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </ChartWrapper>
    );
}

// Market Heatmap
export function MarketHeatmap({ data }: { data: any[] }) {
    const [mounted, setMounted] = useState(false);
    useEffect(() => { setMounted(true); }, []);
    if (!mounted) return <div className="card-terminal animate-pulse h-[420px]" />;

    return (
        <ChartWrapper title="Market Density (Brand x Category)" iconColor="bg-[#10B981]" fullWidth>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2 h-full overflow-y-auto pr-2 custom-scrollbar">
                {data.map((cell, i) => (
                    <div
                        key={i}
                        className="p-3 bg-[#0B1120] border border-[#1E293B] rounded flex flex-col justify-between hover:border-[#3B82F6] transition-all group"
                        title={`${cell.brand} - ${cell.product_type}: ${cell.value} Units Sold`}
                    >
                        <div className="flex flex-col">
                            <span className="text-[10px] font-mono font-bold text-[#E2E8F0] group-hover:text-[#3B82F6] truncate">
                                {cell.brand}
                            </span>
                            <span className="text-[9px] text-[#94A3B8] uppercase truncate opacity-50 mt-0.5">{cell.product_type}</span>
                        </div>
                        <div className="mt-2 flex items-baseline justify-between border-t border-[#1E293B] pt-2">
                            <span className="text-[8px] text-[#94A3B8] uppercase">Density</span>
                            <div className="flex gap-1 items-baseline">
                                <span className="text-sm font-mono font-bold text-[#3B82F6]">{cell.value.toLocaleString()}</span>
                                <span className="text-[8px] text-[#1E293B] font-bold">UNITS</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </ChartWrapper>
    );
}

// Category Donut
export function CategoryDonut({ data }: { data: any[] }) {
    const [mounted, setMounted] = useState(false);
    useEffect(() => { setMounted(true); }, []);
    if (!mounted) return <div className="card-terminal animate-pulse h-[480px]" />;

    // Group by Top 10 + Others
    const sortedData = [...data].sort((a, b) => (b.count || 0) - (a.count || 0));
    const top10Data = sortedData.slice(0, 10);
    const othersData = sortedData.slice(10);
    const othersSum = othersData.reduce((sum, item) => sum + (item.count || 0), 0);

    const donutData = top10Data.map(d => ({
        name: d.name,
        value: d.count
    }));

    if (othersSum > 0) {
        donutData.push({ name: 'Others', value: othersSum });
    }

    const totalCount = donutData.reduce((sum, item) => sum + (item.value || 0), 0);

    const renderLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
        const RADIAN = Math.PI / 180;
        const radius = innerRadius + (outerRadius - innerRadius) * 1.4;
        const x = cx + radius * Math.cos(-midAngle * RADIAN);
        const y = cy + radius * Math.sin(-midAngle * RADIAN);
        if (percent < 0.03) return null;
        return (
            <text x={x} y={y} fill="#E2E8F0" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central" fontSize={9} fontFamily="var(--font-mono)">
                {`${(percent * 100).toFixed(1)}%`}
            </text>
        );
    };

    return (
        <ChartWrapper title="Category Share" iconColor="bg-[#EC4899]">
            <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                    <Pie
                        data={donutData}
                        cx="50%"
                        cy="45%"
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={5}
                        dataKey="value"
                        nameKey="name"
                        stroke="none"
                        label={renderLabel}
                        labelLine={false}
                    >
                        {donutData.map((_, index) => (
                            <Cell key={`cell-${index}`} fill={CHART_PALETTE[index % CHART_PALETTE.length]} />
                        ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend
                        iconType="circle"
                        layout="horizontal"
                        verticalAlign="bottom"
                        align="center"
                        wrapperStyle={{ fontSize: '9px', fontFamily: 'var(--font-mono)', paddingBottom: '20px' }}
                        formatter={(value, entry: any) => {
                            const item = donutData.find(d => d.name === value);
                            const pct = item && totalCount > 0 ? ((item.value / totalCount) * 100).toFixed(1) : '0';
                            return `${value} (${pct}%)`;
                        }}
                    />
                </PieChart>
            </ResponsiveContainer>
        </ChartWrapper>
    );
}
