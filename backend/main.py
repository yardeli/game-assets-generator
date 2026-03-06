"""
Game Assets Generator - Simplified Backend
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

# Initialize FastAPI
app = FastAPI(
    title="Game Assets Generator API",
    description="AI-powered 3D game asset generation",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated files
Path("outputs").mkdir(exist_ok=True)
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# Database setup
DB_PATH = "./assets.db"

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS generations (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        prompt TEXT,
        style TEXT,
        status TEXT,
        model_url TEXT,
        preview_url TEXT,
        format TEXT,
        created_at TIMESTAMP,
        completed_at TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS assets (
        id TEXT PRIMARY KEY,
        generation_id TEXT,
        title TEXT,
        format TEXT,
        url TEXT,
        size INTEGER,
        created_at TIMESTAMP,
        FOREIGN KEY (generation_id) REFERENCES generations(id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Pydantic models
class GenerateRequest(BaseModel):
    prompt: str
    style: Optional[str] = "realistic"
    format: Optional[str] = "glb"
    user_id: Optional[str] = "default"

class GenerationResponse(BaseModel):
    id: str
    status: str
    prompt: str
    style: str
    created_at: str

# Routes
@app.get("/api/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "Game Assets Generator API"
    }

@app.post("/api/generate", response_model=GenerationResponse)
async def generate_asset(request: GenerateRequest, background_tasks: BackgroundTasks):
    """Generate a 3D gaming asset from text prompt"""
    generation_id = str(uuid.uuid4())
    
    try:
        # Store generation record
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO generations (id, user_id, prompt, style, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (generation_id, request.user_id, request.prompt, request.style, "pending", datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        # Start generation in background
        background_tasks.add_task(
            process_generation,
            generation_id,
            request.prompt,
            request.style,
            request.format
        )
        
        return GenerationResponse(
            id=generation_id,
            status="pending",
            prompt=request.prompt,
            style=request.style,
            created_at=datetime.now().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_generation(generation_id: str, prompt: str, style: str, format: str):
    """Process asset generation using 3D pipeline"""
    try:
        # Use the real 3D generation pipeline
        from generate_3d import get_generator
        
        generator = get_generator()
        result = generator.generate(prompt, style, format, generation_id)
        
        # Update database with result
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if result["status"] == "completed":
            cursor.execute('''
            UPDATE generations
            SET status = ?, model_url = ?, preview_url = ?, format = ?, completed_at = ?
            WHERE id = ?
            ''', (
                "completed",
                result["model_url"],
                result["preview_url"],
                format,
                datetime.now().isoformat(),
                generation_id
            ))
        else:
            cursor.execute('''
            UPDATE generations
            SET status = ?, completed_at = ?
            WHERE id = ?
            ''', ("failed", datetime.now().isoformat(), generation_id))
        
        conn.commit()
        conn.close()
        
        print(f"[OK] Generation completed: {generation_id}")
        
    except Exception as e:
        print(f"[ERR] Generation failed: {e}")
        import traceback
        traceback.print_exc()
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('UPDATE generations SET status = ? WHERE id = ?', ("failed", generation_id))
            conn.commit()
            conn.close()
        except:
            pass

@app.get("/api/generation/{generation_id}")
async def get_generation_status(generation_id: str):
    """Get status of a generation"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM generations WHERE id = ?', (generation_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    return dict(result)

@app.get("/api/assets")
async def get_user_assets(user_id: str = "default"):
    """Get user's asset library"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT a.id, a.title, a.format, a.url, a.created_at
    FROM assets a
    JOIN generations g ON a.generation_id = g.id
    WHERE g.user_id = ?
    ORDER BY a.created_at DESC
    ''', (user_id,))
    
    assets = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {"assets": assets, "count": len(assets)}

@app.post("/api/assets/{generation_id}/save")
async def save_asset(generation_id: str, title: str):
    """Save generated asset to user library"""
    import uuid
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM generations WHERE id = ?', (generation_id,))
    generation = cursor.fetchone()
    
    if not generation:
        conn.close()
        raise HTTPException(status_code=404, detail="Generation not found")
    
    asset_id = str(uuid.uuid4())
    cursor.execute('''
    INSERT INTO assets (id, generation_id, title, format, url, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (asset_id, generation_id, title, "glb", "", datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return {"asset_id": asset_id, "title": title}

@app.get("/api/stats")
async def get_stats(user_id: str = "default"):
    """Get user generation stats"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM generations WHERE user_id = ?', (user_id,))
    total_generations = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM generations WHERE user_id = ? AND status = ?', (user_id, "completed"))
    completed = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM assets WHERE generation_id IN (SELECT id FROM generations WHERE user_id = ?)', (user_id,))
    saved_assets = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_generations": total_generations,
        "completed": completed,
        "saved_assets": saved_assets,
        "success_rate": round((completed / total_generations * 100) if total_generations > 0 else 0, 1)
    }

@app.get("/api/styles")
async def get_available_styles():
    """Get available art styles"""
    return {
        "styles": [
            "realistic",
            "stylized",
            "low-poly",
            "cartoon",
            "fantasy",
            "sci-fi",
            "voxel",
            "anime"
        ]
    }

@app.get("/api/formats")
async def get_export_formats():
    """Get supported export formats"""
    return {
        "formats": [
            {"name": "GLB", "ext": "glb", "description": "Standard glTF binary format"},
            {"name": "OBJ", "ext": "obj", "description": "Wavefront OBJ format"},
            {"name": "GLTF", "ext": "gltf", "description": "glTF JSON format"},
            {"name": "FBX", "ext": "fbx", "description": "Autodesk FBX format"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
