# Deployment Guide (Supabase Optimized)

This document provides instructions for deploying the **Personal Care Analytical Console** components. This setup assumes you are using **Supabase** for your PostgreSQL database.

## 1. Database Setup (Supabase)
1. **Create Project**: Sign up at [Supabase](https://supabase.com).
2. **Schema**: Go to the "SQL Editor" in Supabase and run the content of `database/schema.sql`.
3. **Connection Details**: Go to **Project Settings > Database** to find your connection string and parameters.

---

## 2. Backend Deployment (Koyeb)
The backend is a Go application located in `/backend`.

### Steps:
1. **Create Account**: [Koyeb.com](https://www.koyeb.com).
2. **New Service**: Select **GitHub** source.
3. **Configuration**:
   - **Work Directory**: `backend`
   - **Build Command**: `go build -o market_dashboard ./cmd/server`
   - **Run Command**: `./market_dashboard`
4. **Environment Variables**: Use the "Transaction Connection" or "Connection Parameters" from Supabase:
   - `DATABASE_URL`: Your Supabase connection string
   - `DB_HOST`: Supabase Host (e.g., `db.your-id.supabase.co`)
   - `DB_PORT`: `5432` or `6543`
   - `DB_USER`: `postgres`
   - `DB_PASSWORD`: Your project password
   - `DB_NAME`: `postgres`
   - `PORT`: `8000`

---

## 3. Frontend Deployment (Vercel)
The frontend is a Next.js application in `/frontend`.

### Steps:
1. **Import GitHub**: Connect repo to [Vercel](https://vercel.com).
2. **Settings**:
   - **Root Directory**: `frontend`
3. **Environment Variables**:
   - `NEXT_PUBLIC_API_URL`: Your deployed Koyeb API URL.

---

## 4. ETL Automation (GitHub Actions)
Located in `etl/`.

### Steps:
1. **GitHub Secrets**: Add `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` (from Supabase) to your GitHub repository secrets.
2. **Execution**: The workflow in `.github/workflows/etl.yml` runs daily:
   - **Extract**: Scrapes TikTok Shop (`etl/tiktokshop_scraper.py`).
   - **Transform**: Cleans data to CSV (`etl/tiktokshop_transform.py`).
   - **Load**: Syncs CSV to Supabase (`etl/tiktokshop_load.py`).

### Local ETL Run:
```bash
# From the project root:
python etl/run_etl.py
```
