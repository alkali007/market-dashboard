# Personal Care Analytical Console
### Market Intelligence Dashboard for TikTok Shop

A full-stack market intelligence platform that scrapes, processes, and visualizes TikTok Shop data for the Personal Care industry.

## 🏗️ Architecture Overview

The project is built with a modular **ETL-First** philosophy:

### 1. 📥 Data Extraction (The Scraper)
- **Tech**: Python, Undetected Chromedriver, BeautifulSoup4.
- **Workflow**: Automated navigation to TikTok Shop categories, infinite scroll handling, and raw data extraction in JSON format.
- **Location**: `etl/tiktokshop_scraper.py`

### 2. 🧹 Data Transformation (The Processor)
- **Tech**: Python, Pandas.
- **Workflow**: Cleans raw strings into structured numerical data (prices, sales volumes, ratings), handles currency conversion, and calculates discounts.
- **Location**: `etl/tiktokshop_transform.py`

### 3. 🚀 Data Loading (The Pipeline)
- **Tech**: Python, Psycopg2.
- **Workflow**: Performs advanced enrichment (fuzz matching for brands/models) and upserts data into **Supabase (PostgreSQL)**.
- **Location**: `etl/tiktokshop_load.py` & `pipeline/`

### 4. 🔗 Backend API
- **Tech**: Go (Gin Gonic).
- **Workflow**: High-performance REST API serving aggregated market metrics from Supabase.
- **Location**: `backend/`

### 5. 📊 Frontend Console
- **Tech**: Next.js 15, Recharts, Tailwind CSS.
- **Workflow**: Premium analytical dashboard featuring market heatmaps and interactive filters.
- **Location**: `frontend/`

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Go 1.22+
- Node.js 18+
- Supabase Project

### Installation
1. **Clone the Repo**:
   ```bash
   git clone <your-repo-url>
   ```
2. **Setup ETL**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Setup Backend**:
   ```bash
   cd backend && go mod download
   ```
4. **Setup Frontend**:
   ```bash
   cd frontend && npm install
   ```

### Running Locally
1. Configure your `.env` file at the root with your **Supabase** credentials.
2. Run the ETL: `python etl/run_etl.py`
3. Start Backend: `cd backend && go run ./cmd/server`
4. Start Frontend: `cd frontend && npm run dev`

## 🌐 Deployment
Refer to [DEPLOYMENT.md](./DEPLOYMENT.md) for full instructions on deploying to **Koyeb (Backend)**, **Vercel (Frontend)**, and **GitHub Actions (ETL)**.
