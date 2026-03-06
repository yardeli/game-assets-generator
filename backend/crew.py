"""
Game Assets Generator - 2D to 3D Local Pipeline
Converts text prompts → 2D images → 3D meshes using Stable Diffusion + depth mapping
No external APIs required - everything runs locally!
"""

import os
import uuid
import numpy as np
from typing import Dict
from pathlib import Path
import torch
from PIL import Image

# Create output directories
Path("outputs").mkdir(exist_ok=True)
Path("outputs/images").mkdir(exist_ok=True)
Path("outputs/models").mkdir(exist_ok=True)

class GameAssetsPipeline:
    """
    Local 2D-to-3D generation pipeline
    1. Text → 2D Image (Stable Diffusion)
    2. 2D Image → Depth Map (Intel DPT)
    3. Depth Map → 3D Mesh (Trimesh)
    """
    
    def __init__(self):
        """Initialize models"""
        print("[INIT] Loading Stable Diffusion...")
        try:
            from diffusers import StableDiffusionPipeline
            self.sd_pipe = StableDiffusionPipeline.from_pretrained(
                "stabilityai/stable-diffusion-2-1-small",
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )
            if torch.cuda.is_available():
                self.sd_pipe = self.sd_pipe.to("cuda")
            print("[OK] Stable Diffusion loaded!")
        except Exception as e:
            print(f"[WARN] Could not load Stable Diffusion: {e}")
            self.sd_pipe = None
        
        print("[INIT] Loading depth estimation model...")
        try:
            from transformers import AutoImageProcessor, AutoModelForDepthEstimation
            self.depth_processor = AutoImageProcessor.from_pretrained("Intel/dpt-large")
            self.depth_model = AutoModelForDepthEstimation.from_pretrained("Intel/dpt-large")
            if torch.cuda.is_available():
                self.depth_model = self.depth_model.to("cuda")
            print("[OK] Depth model loaded!")
        except Exception as e:
            print(f"[WARN] Could not load depth model: {e}")
            self.depth_model = None
            self.depth_processor = None
    
    def text_to_image(self, prompt: str) -> Image.Image:
        """Step 1: Generate 2D image from text prompt"""
        if not self.sd_pipe:
            print("[WARN] Stable Diffusion not available, creating placeholder image")
            return self._create_placeholder_image(prompt)
        
        try:
            print(f"[STEP1] Generating image for: {prompt}")
            image = self.sd_pipe(
                prompt,
                num_inference_steps=25,
                height=512,
                width=512,
                guidance_scale=7.5
            ).images[0]
            print("[OK] Image generated!")
            return image
        except Exception as e:
            print(f"[WARN] Image generation failed: {e}")
            return self._create_placeholder_image(prompt)
    
    def image_to_depth_map(self, image: Image.Image) -> np.ndarray:
        """Step 2: Generate depth map from 2D image"""
        if not self.depth_model:
            print("[WARN] Depth model not available, using edge detection")
            return self._edge_based_depth(image)
        
        try:
            print("[STEP2] Estimating depth...")
            inputs = self.depth_processor(images=image, return_tensors="pt")
            
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.depth_model(**inputs)
                predicted_depth = outputs.predicted_depth
            
            # Normalize depth map
            depth_map = (predicted_depth - predicted_depth.min()) / (predicted_depth.max() - predicted_depth.min())
            depth_map = depth_map.squeeze().cpu().numpy()
            print("[OK] Depth map generated!")
            return depth_map
        except Exception as e:
            print(f"[WARN] Depth estimation failed: {e}")
            return self._edge_based_depth(image)
    
    def depth_to_mesh(self, image: Image.Image, depth_map: np.ndarray) -> tuple:
        """Step 3: Convert depth map to 3D mesh"""
        try:
            import trimesh
            from scipy.ndimage import gaussian_filter
            
            print("[STEP3] Building 3D mesh...")
            
            # Smooth depth map
            depth_smooth = gaussian_filter(depth_map, sigma=2)
            
            # Create vertex grid
            height, width = depth_smooth.shape
            x = np.linspace(0, 1, width)
            y = np.linspace(0, 1, height)
            xx, yy = np.meshgrid(x, y)
            
            # Stack into vertices (scale depth)
            vertices = np.dstack((xx, yy, depth_smooth * 0.5))
            vertices = vertices.reshape(-1, 3)
            
            # Create faces (simple grid)
            faces = []
            for i in range(height - 1):
                for j in range(width - 1):
                    v0 = i * width + j
                    v1 = i * width + j + 1
                    v2 = (i + 1) * width + j
                    v3 = (i + 1) * width + j + 1
                    
                    faces.append([v0, v1, v2])
                    faces.append([v1, v3, v2])
            
            faces = np.array(faces)
            
            # Create trimesh
            mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
            mesh.smooth()
            
            # Color from original image
            image_array = np.array(image.resize((width, height))) / 255.0
            if image_array.ndim == 3:
                colors = image_array
            else:
                colors = np.stack([image_array] * 3, axis=-1)
            
            print("[OK] Mesh created!")
            return mesh, colors
        except Exception as e:
            print(f"[WARN] Mesh creation failed: {e}")
            return None, None
    
    def export_model(self, mesh, colors, generation_id: str, format: str = "glb") -> str:
        """Step 4: Export mesh to file"""
        if mesh is None:
            return None
        
        try:
            print(f"[STEP4] Exporting as {format.upper()}...")
            
            output_path = f"outputs/models/{generation_id}.{format}"
            
            if format == "glb":
                mesh.export(output_path)
            elif format == "obj":
                mesh.export(output_path)
            elif format == "gltf":
                mesh.export(output_path.replace(".gltf", ".glb"))
            
            print(f"[OK] Exported to {output_path}")
            return output_path
        except Exception as e:
            print(f"[WARN] Export failed: {e}")
            return None
    
    def execute_generation(self, prompt: str, style: str, format: str, generation_id: str) -> Dict:
        """
        Execute full pipeline: Text → Image → Depth → Mesh → Export
        """
        try:
            print(f"\n[START] Generation: {generation_id}")
            print(f"        Prompt: {prompt}")
            print(f"        Style: {style}")
            
            # Step 1: Generate 2D image
            image = self.text_to_image(f"{prompt}, {style} style, high quality, detailed")
            
            # Save 2D image preview
            image_path = f"outputs/images/{generation_id}.png"
            image.save(image_path)
            
            # Step 2: Estimate depth
            depth_map = self.image_to_depth_map(image)
            
            # Step 3: Create 3D mesh
            mesh, colors = self.depth_to_mesh(image, depth_map)
            
            # Step 4: Export
            model_path = self.export_model(mesh, colors, generation_id, format)
            
            if model_path:
                return {
                    "status": "completed",
                    "generation_id": generation_id,
                    "model_url": f"http://localhost:8000/outputs/models/{generation_id}.{format}",
                    "preview_url": f"http://localhost:8000/outputs/images/{generation_id}.png",
                    "format": format,
                    "message": f"[OK] Generated {generation_id}"
                }
            else:
                return {
                    "status": "failed",
                    "generation_id": generation_id,
                    "error": "Export failed"
                }
        
        except Exception as e:
            print(f"[ERROR] Generation failed: {e}")
            return {
                "status": "failed",
                "generation_id": generation_id,
                "error": str(e)
            }
    
    def _create_placeholder_image(self, prompt: str) -> Image.Image:
        """Create placeholder image when SD unavailable"""
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGB', (512, 512), color=(100, 100, 150))
        draw = ImageDraw.Draw(img)
        draw.text((50, 250), f"Placeholder: {prompt[:30]}", fill=(255, 255, 255))
        return img
    
    def _edge_based_depth(self, image: Image.Image) -> np.ndarray:
        """Create depth map from image edges (fallback)"""
        from PIL import Image, ImageFilter
        
        # Convert to grayscale
        gray = image.convert('L')
        
        # Edge detection
        edges = gray.filter(ImageFilter.FIND_EDGES)
        depth = np.array(edges) / 255.0
        
        # Smooth
        from scipy.ndimage import gaussian_filter
        depth = gaussian_filter(depth, sigma=3)
        
        return depth


# Create global pipeline instance - lazy loading (on first request)
pipeline = None

def get_pipeline():
    """Get or initialize pipeline (lazy loading)"""
    global pipeline
    if pipeline is None:
        print("[INIT] Initializing pipeline on first request...")
        pipeline = GameAssetsPipeline()
    return pipeline


# Backwards compatibility wrapper (for API calls)
class GameAssetsCrew:
    """Wrapper for API compatibility"""
    
    def execute_generation(self, prompt: str, style: str, format: str, generation_id: str) -> Dict:
        """Execute generation using the local pipeline"""
        p = get_pipeline()
        return p.execute_generation(prompt, style, format, generation_id)
