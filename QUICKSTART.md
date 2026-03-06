# ⚡ Quick Start Guide

Get Game Assets Generator running in **5 minutes**.

## Step 1: Clone & Setup (2 min)

```bash
# Clone
git clone https://github.com/yardeli/game-assets-generator.git
cd game-assets-generator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure API Keys (1 min)

```bash
# Copy template
cp .env.example .env

# Edit .env and add your keys:
nano .env
```

**Required:**
- `OPENAI_API_KEY=sk-...` — Get from https://platform.openai.com


## Step 3: Start Backend (1 min)

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

You should see:
```
Uvicorn running on http://127.0.0.1:8000
```

## Step 4: Start Frontend (1 min)

In a new terminal:

```bash
# From project root
cd frontend
python -m http.server 3000
```

You should see:
```
Serving HTTP on 0.0.0.0 port 3000 ...
```

## Step 5: Open & Test!

Open your browser:
```
http://localhost:3000
```

### Try This First

1. Enter prompt: `A wooden shield, fantasy style`
2. Select style: `Realistic`
3. Select format: `GLB`
4. Click **Generate Asset**
5. Wait for completion
6. Download or save!

## 🎉 You're Running!

Both servers are now live. You can:
- ✨ Generate assets
- 📚 View your library
- 📋 Check generation history
- 📊 See your stats

## 🆘 Troubleshooting

### Port Already in Use

```bash
# Change port
python -m uvicorn main:app --port 8001

# Or kill existing process
lsof -ti:8000 | xargs kill -9
```

### API Key Errors

```
ModuleNotFoundError: No module named 'openai'
```

→ Run: `pip install -r requirements.txt` again

### CORS Issues

If frontend can't reach backend, make sure `main.py` has CORS enabled:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Database Errors

```bash
# Reset database
rm assets.db
python -c "from backend.main import init_db; init_db()"
```

## 📚 Next Steps

1. **Read the main README** — Full feature overview
2. **Check DEPLOY.md** — Deploy to production
3. **Explore the code** — Understand CrewAI integration
4. **Customize styles** — Add your own art styles

## 💡 Pro Tips

### Generate Multiple Assets

```
Prompt 1: Dragon sword
Prompt 2: Dragon shield
Prompt 3: Dragon armor

All in style: Fantasy, seed: 12345
→ Consistent art style across all!
```

### Check Generation Status

```bash
curl http://localhost:8000/api/generation/{id}
```

### Batch Export

```bash
# Save all assets
for asset in assets/*; do
  curl -o "$asset.glb" http://localhost:8000/api/assets/$asset
done
```

## 🚀 Ready to Deploy?

See [DEPLOY.md](./DEPLOY.md) for:
- Vercel (frontend)
- Railway/Heroku (backend)
- Docker
- Production checklist

---

**Questions?** Check the main README or open an issue!
