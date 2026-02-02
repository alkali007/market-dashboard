# Deployment Guide (Supabase Optimized)

This document provides instructions for deploying the **Personal Care Analytical Console** components. This setup assumes you are using **Supabase** for your PostgreSQL database.

## 1. Database Setup (Supabase)
1. **Create Project**: Sign up at [Supabase](https://supabase.com).
2. **Schema**: Go to the "SQL Editor" in Supabase and run the content of `database/schema.sql`.
3. **Connection Details**: Go to **Project Settings > Database** to find your connection string and parameters.

---

## 2. Backend Deployment (Railway.com)
The backend is a Go application located in `/backend`.

### Steps:
1. **Create Account**: [Railway.app](https://railway.app).
2. **New Project**: Select **Deploy from GitHub repo**.
3. **Configuration**:
   - Railway will automatically detect the Go project.
   - Go to **Settings > General > Root Directory** and set it to `backend`.
4. **Environment Variables**:
   - `DATABASE_URL`: Your Supabase connection string.
   - `PORT`: (Optional) Railway provides this automatically, but you can set it to `8080`.
5. **Custom Domain**: In the **Settings** tab, generate a domain or add your own.

---

## 3. Frontend Deployment (Vercel)
The frontend is a Next.js application in `/frontend`.

### Steps:
1. **Import GitHub**: Connect repo to [Vercel](https://vercel.com).
2. **Settings**:
   - **Root Directory**: `frontend`
3. **Environment Variables**:
   - `NEXT_PUBLIC_API_URL`: Your deployed Railway API URL (e.g., `https://backend-production-xyz.up.railway.app`).

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
