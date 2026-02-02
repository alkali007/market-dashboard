import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
    const { searchParams } = new URL(request.url);
    const path = searchParams.get('path');

    if (!path) {
        return NextResponse.json({ error: 'Missing path parameter' }, { status: 400 });
    }

    // Use server-side only environment variables (no NEXT_PUBLIC_ prefix)
    const apiUrl = process.env.RAILWAY_API_URL || 'http://localhost:8080';
    const apiKey = process.env.API_KEY || '';

    // Get all search params except 'path' to forward to the backend
    const forwardParams = new URLSearchParams();
    searchParams.forEach((value, key) => {
        if (key !== 'path') {
            forwardParams.append(key, value);
        }
    });

    const queryString = forwardParams.toString();
    const targetUrl = `${apiUrl}${path}${queryString ? '?' + queryString : ''}`;

    try {
        const response = await fetch(targetUrl, {
            method: 'GET',
            headers: {
                'X-API-Key': apiKey,
                'Content-Type': 'application/json',
            },
        });

        const data = await response.json();
        return NextResponse.json(data, { status: response.status });
    } catch (error) {
        console.error('Proxy Error:', error);
        return NextResponse.json({ error: 'Failed to fetch from backend' }, { status: 500 });
    }
}
