# 🎮 Game Assets Generator

**Convert text prompts into production-ready 3D gaming assets with AI.**

An intelligent web platform that uses CrewAI to orchestrate a multi-agent system for generating, optimizing, and exporting professional 3D game assets from simple text descriptions.

## ✨ Features

- **🤖 AI-Powered Generation** — Convert any text prompt into a 3D model
- **🎨 Style Control** — Choose from realistic, cartoon, low-poly, fantasy, sci-fi, and more
- **📦 Multiple Formats** — Export to GLB, OBJ, GLTF, and FBX
- **⚡ Game-Ready Output** — Optimized models with normal maps and proper geometry
- **📚 Asset Library** — Organize and manage your generated assets
- **📊 Smart Analytics** — Track your generation history and success rates
- **🔧 CrewAI Architecture** — Multi-agent system for intelligent processing

## 🏗️ Architecture

```
Frontend (React + Three.js)
    ↓
FastAPI Backend
    ↓
CrewAI Multi-Agent System
    ├─ Prompt Analyzer — Interprets user requests
    ├─ 3D Generator — Calls Meshy/Tripo API
    ├─ Optimizer — Reduces polygons, generates normal maps
    └─ Exporter — Converts to game-ready formats
    ↓
Meshy API (3D Generation)
    ↓
SQLite Database (Asset Storage)
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js (optional, for frontend dev)
- API keys: OpenAI, Anthropic, Meshy (or Tripo)

### Installation

1. **Clone and setup:**
```bash
git clone https://github.com/yourusername/game-assets-generator.git
cd game-assets-generator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure API keys:**
```bash
cp .env.example .env
# Edit .env and add your API keys
OPENAI_API_KEY=sk-...
MESHY_API_KEY=your-key-here
```

4. **Start the backend:**
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

5. **Start the frontend:**
```bash
# In another terminal, from the project root
cd frontend
python -m http.server 3000
```

6. **Open in browser:**
```
http://localhost:3000
```

## 📖 Usage

### Generate an Asset

1. Enter a prompt: *"A wooden sword with a dragon handle"*
2. Choose art style: *"Fantasy"*
3. Select format: *"GLB"*
4. Click **Generate Asset**
5. Wait for processing (typically 30-120 seconds)
6. Download or save to library

### Examples

```
"A rusted iron sword with a leather grip, medieval fantasy style"
→ Downloads as sword.glb, game-ready, 100k polygons

"A wooden treasure chest, ornate carvings, aged wood, low-poly"
→ Optimized with 50k polygons, perfect for indie games

"A sci-fi robot character, metallic blue, standing pose"
→ Character model with rigged skeleton, ready for animation
```

## 📚 API Endpoints

### Generation

```
POST /api/generate
{
  "prompt": "A dragon statue",
  "style": "fantasy",
  "format": "glb",
  "user_id": "default"
}
→ Returns: { id, status, created_at, ... }
```

### Status & Retrieval

```
GET /api/generation/{id}        # Check generation status
GET /api/assets                  # User's asset library
GET /api/stats                   # User statistics
GET /api/styles                  # Available art styles
GET /api/formats                 # Supported export formats
```

### Asset Management

```
POST /api/assets/{id}/save       # Save to library
GET /api/generation/{id}         # Download completed model
```

## 🧠 CrewAI Crew System

The backend uses CrewAI to orchestrate intelligent asset generation:

### Agents

1. **Prompt Analyst**
   - Interprets user prompts
   - Extracts key details
   - Recommends optimization level

2. **3D Model Generator**
   - Calls Meshy API
   - Monitors generation progress
   - Handles errors gracefully

3. **Model Optimizer**
   - Reduces polygon count
   - Generates normal maps
   - Creates LOD versions

4. **Asset Exporter**
   - Converts to requested format
   - Validates exports
   - Generates metadata

### Example Crew Execution

```python
from crew import GameAssetsCrew

crew = GameAssetsCrew()
result = crew.execute_generation(
    prompt="A dragon",
    style="fantasy",
    format="glb",
    generation_id="gen-123"
)
# Returns: { status, model_url, preview_url, ... }
```

## 🔌 Integration with 3D APIs

### Meshy API

```python
response = requests.post(
    "https://api.meshy.ai/v1/text-to-3d",
    headers={"Authorization": f"Bearer {MESHY_API_KEY}"},
    json={
        "prompt": "A dragon",
        "art_style": "fantasy"
    }
)
```

### Tripo API (Alternative)

```python
response = requests.post(
    "https://api.tripo3d.com/v1/text-to-model",
    headers={"Authorization": f"Bearer {TRIPO_API_KEY}"},
    json={"prompt": "A dragon"}
)
```

## 🎯 Advanced Features

### Style Locking

```python
# Generate multiple assets with consistent style
"Gothic Sword"    # seed: 12345
"Gothic Shield"   # seed: 12345 (same style)
"Gothic Helmet"   # seed: 12345 (consistent!)
```

### Normal Map Generation

Every exported model includes:
- Albedo texture
- Normal map (for dynamic lighting)
- Roughness map

### Asset Library Management

- Auto-tagging: "fantasy", "low-poly", "medieval"
- Search and filter
- Version history
- Bulk operations

## 📦 Deployment

### Vercel (Frontend)

```bash
vercel deploy --prod
```

### Railway/Heroku (Backend)

```bash
git push heroku main
```

### Docker

```bash
docker build -t game-assets-generator .
docker run -p 8000:8000 game-assets-generator
```

See [DEPLOY.md](./DEPLOY.md) for detailed instructions.

## 🛠️ Development

### Project Structure

```
game-assets-generator/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── crew.py              # CrewAI agents
│   ├── database.py          # Database setup
│   └── models.py            # Pydantic models
├── frontend/
│   ├── index.html           # Main HTML
│   ├── app.js               # React components
│   └── style.css            # Styling
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
├── README.md               # This file
└── DEPLOY.md              # Deployment guide
```

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
black backend/
flake8 backend/
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

MIT License — See LICENSE file

## 🆘 Support

- **Issues:** GitHub Issues
- **Documentation:** [Wiki](https://github.com/yourrepo/wiki)
- **Email:** support@gameassets.ai

## 🚀 Roadmap

- [ ] Batch generation API
- [ ] Real-time preview with Three.js
- [ ] Animation generation (walk cycles, attacks)
- [ ] Texture upscaling (4x, 8x)
- [ ] Voxel export (MagicaVoxel format)
- [ ] Game engine plugins (Unity, Unreal, Godot)
- [ ] Commercial license pricing
- [ ] Team collaboration features

## 🎮 Made with ❤️ by the Game Assets Team

---

**Start generating! Create your first 3D asset today.** 🎨✨
