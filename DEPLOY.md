# 🚀 Deployment Guide

Deploy Game Assets Generator to production.

## Frontend Deployment (Vercel)

### Option 1: One-Click Import

1. Go to https://vercel.com/new/import
2. Paste: `https://github.com/yourusername/game-assets-generator`
3. Click "Import"
4. Select `frontend` as root directory
5. Click "Deploy"

### Option 2: Vercel CLI

```bash
npm i -g vercel
cd frontend
vercel
```

### Result

Your frontend will be at:
```
https://game-assets-generator-[your-name].vercel.app
```

## Backend Deployment (Railway)

### Step 1: Push to GitHub

```bash
git remote add origin https://github.com/yourusername/game-assets-generator.git
git push -u origin main
```

### Step 2: Deploy to Railway

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub"
3. Select your repo
4. Wait for auto-detection (should find FastAPI app)
5. Add environment variables (from `.env`)
6. Click "Deploy"

### Step 3: Set Domain

In Railway dashboard:
- Go to "Settings"
- Copy the public URL
- Update frontend API base to this URL

### Result

Your backend will be at:
```
https://your-app-[random].railway.app
```

## Backend Deployment (Heroku)

### Step 1: Create Heroku App

```bash
heroku create your-app-name
```

### Step 2: Add Buildpack

```bash
heroku buildpacks:add heroku/python
```

### Step 3: Set Environment Variables

```bash
heroku config:set OPENAI_API_KEY=sk-...
heroku config:set MESHY_API_KEY=...
heroku config:set ANTHROPIC_API_KEY=sk-ant-...
```

### Step 4: Deploy

```bash
git push heroku main
```

### Result

Your backend will be at:
```
https://your-app-name.herokuapp.com
```

## Docker Deployment

### Build Docker Image

```bash
docker build -t game-assets-generator .
docker tag game-assets-generator yourusername/game-assets-generator:latest
```

### Push to Docker Hub

```bash
docker login
docker push yourusername/game-assets-generator:latest
```

### Deploy to Cloud Run (Google Cloud)

```bash
gcloud run deploy game-assets-generator \
  --image yourusername/game-assets-generator:latest \
  --platform managed \
  --region us-central1 \
  --set-env-vars OPENAI_API_KEY=sk-...,MESHY_API_KEY=...
```

## Production Configuration

### Update Frontend API Base

In `frontend/app.js`, change:

```javascript
const API_BASE = process.env.REACT_APP_API_URL || "https://your-backend.railway.app/api";
```

### Enable HTTPS

```python
# backend/main.py
app = FastAPI(
    title="Game Assets Generator",
    openapi_url="/api/openapi.json",
)

# SSL cert will be handled by hosting provider (Vercel, Railway)
```

### Database Migration

For production, switch from SQLite to PostgreSQL:

1. **Create PostgreSQL database:**
   - Railway: Auto-provisioned
   - Heroku: `heroku addons:create heroku-postgresql:standard-0`

2. **Update connection string:**
   ```python
   # backend/main.py
   DATABASE_URL = os.getenv(
       "DATABASE_URL",
       "postgresql://user:pass@localhost/assets"
   )
   ```

3. **Install psycopg2:**
   ```bash
   pip install psycopg2-binary
   ```

## Environment Variables

### Required (Production)

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
MESHY_API_KEY=...
DATABASE_URL=postgresql://...
```

### Optional

```bash
CREWAI_MODEL=gpt-4
CREWAI_VERBOSE=False
DEBUG=False
```

## Monitoring

### Railway Dashboard

- Real-time logs
- Deployment history
- CPU/memory usage
- Crash detection

### Vercel Analytics

- Edge function performance
- Core Web Vitals
- Traffic analytics
- Error tracking

### Error Tracking (Optional)

Add Sentry for error monitoring:

```bash
pip install sentry-sdk

# In main.py
import sentry_sdk
sentry_sdk.init("https://key@sentry.io/123")
```

## Performance Optimization

### Frontend

```bash
# Build production bundle
npm run build

# Or Python server
cd frontend
python -m http.server 3000
```

### Backend

```bash
# Use production ASGI server
pip install gunicorn

# Run
gunicorn backend.main:app -w 4 -b 0.0.0.0:8000
```

### Caching

```python
# backend/main.py
from fastapi_cache2 import FastAPICache2
from fastapi_cache2.backends.redis import RedisBackend

# Cache API responses
@app.get("/api/styles")
@cached(expire=3600)
async def get_styles():
    ...
```

## SSL/TLS

All major hosting providers (Vercel, Railway, Heroku) include free SSL by default.

## Backup & Recovery

### Database Backups

```bash
# Railway: Auto-backed up
# Heroku: heroku pg:backups

# Manual backup
pg_dump $DATABASE_URL > backup.sql
```

### Disaster Recovery Plan

1. ✅ Database backups daily
2. ✅ Code in GitHub
3. ✅ Environment variables documented
4. ✅ One-click redeploy scripts

## Testing Deployment

Before going live:

```bash
# Test locally with production settings
DEBUG=False python -m uvicorn backend.main:app

# Test API endpoints
curl https://your-backend.railway.app/api/health
curl https://your-frontend.vercel.app/

# Load test
ab -n 1000 -c 10 https://your-backend.railway.app/api/stats
```

## Cost Estimates

| Service | Tier | Monthly Cost |
|---------|------|-------------|
| Vercel | Pro | $20 |
| Railway | Usage-based | $10-50 |
| PostgreSQL | Railway | $5-10 |
| Meshy API | Pay-per-generation | $0.01-0.10 per model |
| **Total** | | **$35-80/month** |

## Troubleshooting Production Issues

### High Latency

→ Check Meshy API rate limits
→ Consider request queuing

### Out of Memory

→ Increase Railway plan
→ Optimize model processing

### CORS Errors

→ Check frontend API URL matches backend origin
→ Verify CORS middleware enabled

### Database Connection Errors

→ Check DATABASE_URL env var
→ Verify firewall rules
→ Test connection: `psql $DATABASE_URL`

## Scaling

As traffic grows:

1. **Upgrade Railway plan** → More CPU/memory
2. **Add Redis** → Cache responses
3. **Background jobs** → Queue long-running generations
4. **CDN** → Vercel automatically uses Cloudflare
5. **Load balancing** → Railway auto-scales

---

## Production Checklist

- [ ] API keys configured
- [ ] CORS enabled
- [ ] Database migrated to PostgreSQL
- [ ] HTTPS/SSL enabled
- [ ] Error tracking setup (Sentry)
- [ ] Backup strategy documented
- [ ] Monitoring active
- [ ] Rate limiting configured
- [ ] Load testing passed
- [ ] Documentation updated

---

**Ready to go live?** Deploy now and start generating! 🚀
