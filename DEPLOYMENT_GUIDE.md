# Campus Pulse - Production Deployment & Database Migration Guide

This guide describes how to deploy Campus Pulse to production cloud infrastructure (Render, Vercel, Netlify, Railway, or VPS) and configure PostgreSQL.

---

## 🌐 1. Deployment Architecture Overview

- **Frontend:** Static Single-Page Application (SPA) hosted on **Vercel** or **Netlify**.
- **Backend:** FastAPI ASGI Python web service hosted on **Render**, **Railway**, or **AWS/DigitalOcean VPS**.
- **Database:** SQLite (with `PRAGMA foreign_keys = ON` enforced on every connection) or **PostgreSQL** (for multi-worker production scale).

---

## 🚀 2. Backend Deployment (Render / Railway / VPS)

### Environment Variables
Configure the following environment variables in your cloud provider dashboard:

```env
PORT=8000
DATABASE_PATH=storage/campus_pulse.db
CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173,https://your-frontend-domain.vercel.app
JWT_SECRET_KEY=your_secure_random_production_secret_key_change_me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### Build & Start Command
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn api.main:app --host 0.0.0.0 --port 8000`

---

## 💻 3. Frontend Deployment (Vercel / Netlify)

1. Connect your GitHub repository to Vercel/Netlify.
2. Set Build Settings:
   - **Framework Preset:** Vite
   - **Root Directory:** `Frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
3. Environment Variables:
   - Set `VITE_API_BASE_URL=https://your-backend-api.onrender.com`

---

## 🗄️ 4. PostgreSQL Database Migration (Stage 4)

Campus Pulse repository abstraction is designed to swap database backends cleanly.

### Migration Steps to PostgreSQL:
1. Provision a PostgreSQL instance (e.g., Supabase, ElephantSQL, or Render PostgreSQL).
2. Install `psycopg2-binary` or `asyncpg` in python environment:
   ```bash
   pip install psycopg2-binary
   ```
3. Set `DATABASE_URL` environment variable:
   ```env
   DATABASE_URL=postgresql://user:password@hostname:5432/campus_pulse_db
   ```
4. Run schema initializer script:
   ```bash
   python storage/init_db.py
   ```

---

## 🔒 5. Trusted Proxy & Shared Rate Limiting Architecture

### Reverse Proxy Configuration (Nginx / Cloudflare / AWS ALB)
When Campus Pulse is deployed behind a reverse proxy, load balancer, or CDN:
- Configure trusted proxy headers so `X-Forwarded-For` IP extraction only trusts requests coming from configured proxy IPs (`TRUSTED_PROXIES`).
- Ensure Nginx or Cloudflare passes `X-Forwarded-For` and `X-Forwarded-Proto` correctly.

### Rate Limiting Architecture
- **Single-Instance Deployment (Current):** Rate limits are tracked in-process using token-bucket / sliding window algorithms (`middleware/rate_limiter.py`).
- **Multi-Worker / Distributed Deployment:** When scaling across multiple Uvicorn worker processes or cloud containers, rate-limiting should be backed by a shared Redis instance to maintain synchronized request counting across all workers.
