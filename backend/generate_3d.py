"""
3D Asset Generation Pipeline
Text → 2D Image → Depth Map → 3D Mesh
"""

import numpy as np
from pathlib import Path
import torch
from PIL import Image
import uuid

class ThreeDGenerator:
    def __init__(self):
        """Initialize Stable Diffusion and depth estimation models"""
        print("[INIT] Loading Stable Diffusion 2.1...")
        try:
            from diffusers import StableDiffusionPipeline
            self.sd_pipe = StableDiffusionPipeline.from_pretrained(
                "stabilityai/stable-diffusion-2-1-base",
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )
            if torch.cuda.is_available():
                self.sd_pipe = self.sd_pipe.to("cuda")
            print("[OK] Stable Diffusion loaded!")
            self.sd_available = True
        except Exception as e:
            print(f"[WARN] Stable Diffusion not available: {e}")
            self.sd_available = False
        
        print("[INIT] Loading depth estimation model...")
        try:
            from transformers import AutoImageProcessor, AutoModelForDepthEstimation
            self.depth_processor = AutoImageProcessor.from_pretrained("Intel/dpt-hybrid-midas")
            self.depth_model = AutoModelForDepthEstimation.from_pretrained("Intel/dpt-hybrid-midas")
            if torch.cuda.is_available():
                self.depth_model = self.depth_model.to("cuda")
            print("[OK] Depth model loaded!")
            self.depth_available = True
        except Exception as e:
            print(f"[WARN] Depth model not available: {e}")
            self.depth_available = False
    
    def text_to_image(self, prompt: str) -> Image.Image:
        """Generate 2D image from text prompt"""
        if not self.sd_available:
            print("[WARN] Creating placeholder image (SD not available)")
            return self._create_placeholder_image(prompt)
        
        try:
            print(f"[STEP1] Generating image: {prompt}")
            with torch.no_grad():
                image = self.sd_pipe(
                    prompt,
                    num_inference_steps=30,
                    guidance_scale=7.5,
                    height=512,
                    width=512
                ).images[0]
            print("[OK] Image generated!")
            return image
        except Exception as e:
            print(f"[ERROR] Image generation failed: {e}")
            return self._create_placeholder_image(prompt)
    
    def image_to_depth(self, image: Image.Image) -> np.ndarray:
        """Estimate depth map from image"""
        if not self.depth_available:
            print("[WARN] Creating placeholder depth (model not available)")
            return self._create_placeholder_depth(image)
        
        try:
            print("[STEP2] Estimating depth...")
            inputs = self.depth_processor(images=image, return_tensors="pt")
            
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.depth_model(**inputs)
                depth = outputs.predicted_depth
            
            depth_np = depth.squeeze().cpu().numpy()
            # Normalize
            depth_np = (depth_np - depth_np.min()) / (depth_np.max() - depth_np.min() + 1e-6)
            print("[OK] Depth estimated!")
            return depth_np
        except Exception as e:
            print(f"[ERROR] Depth estimation failed: {e}")
            return self._create_placeholder_depth(image)
    
    def depth_to_mesh(self, image: Image.Image, depth: np.ndarray) -> 'trimesh.Trimesh':
        """Convert depth map to 3D mesh"""
        try:
            print("[STEP3] Creating 3D mesh...")
            import trimesh
            from scipy.ndimage import gaussian_filter
            
            # Smooth depth
            depth_smooth = gaussian_filter(depth, sigma=2)
            
            # Scale depth for better mesh
            depth_scaled = depth_smooth * 0.3
            
            # Create vertex grid
            h, w = depth_smooth.shape
            x = np.linspace(-1, 1, w)
            y = np.linspace(-1, 1, h)
            xx, yy = np.meshgrid(x, y)
            
            # Stack vertices
            vertices = np.dstack((xx, yy, depth_scaled))
            vertices = vertices.reshape(-1, 3)
            
            # Create faces (grid triangulation)
            faces = []
            for i in range(h - 1):
                for j in range(w - 1):
                    v0 = i * w + j
                    v1 = i * w + j + 1
                    v2 = (i + 1) * w + j
                    v3 = (i + 1) * w + j + 1
                    
                    faces.append([v0, v1, v2])
                    faces.append([v1, v3, v2])
            
            faces = np.array(faces)
            
            # Create mesh
            mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
            
            # Clean up
            try:
                mesh.remove_unreferenced_vertices()
            except:
                pass
            
            # Recenter
            try:
                mesh.vertices -= mesh.centroid
            except:
                pass
            
            print("[OK] Mesh created!")
            return mesh
        except Exception as e:
            print(f"[ERROR] Mesh creation failed: {e}")
            return None
    
    def generate(self, prompt: str, style: str, format: str, generation_id: str) -> dict:
        """Full pipeline: Text → Image → Depth → Mesh → Export"""
        try:
            print(f"\n[START] Generating 3D asset")
            print(f"        Prompt: {prompt}")
            print(f"        Style: {style}")
            print(f"        Format: {format}")
            
            # Step 1: Generate image
            image = self.text_to_image(f"{prompt}, {style} style, high quality, 3d render")
            
            # Save preview
            Path("outputs/images").mkdir(parents=True, exist_ok=True)
            preview_path = f"outputs/images/{generation_id}.png"
            image.save(preview_path)
            print(f"[OK] Preview saved: {preview_path}")
            
            # Step 2: Estimate depth
            depth = self.image_to_depth(image)
            
            # Step 3: Create mesh
            mesh = self.depth_to_mesh(image, depth)
            
            if mesh is None:
                return {"status": "failed", "error": "Mesh creation failed"}
            
            # Step 4: Export
            Path("outputs/models").mkdir(parents=True, exist_ok=True)
            model_path = f"outputs/models/{generation_id}.{format}"
            
            print(f"[STEP4] Exporting as {format.upper()}...")
            mesh.export(model_path)
            print(f"[OK] Model exported: {model_path}")
            
            return {
                "status": "completed",
                "generation_id": generation_id,
                "model_url": f"http://localhost:8000/outputs/models/{generation_id}.{format}",
                "preview_url": f"http://localhost:8000/outputs/images/{generation_id}.png",
                "format": format,
                "message": f"3D asset generated successfully!"
            }
        
        except Exception as e:
            print(f"[ERROR] Generation failed: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "failed", "error": str(e)}
    
    def _create_placeholder_image(self, prompt: str) -> Image.Image:
        """Create placeholder when SD unavailable"""
        from PIL import ImageDraw
        img = Image.new('RGB', (512, 512), color=(100, 150, 200))
        draw = ImageDraw.Draw(img)
        draw.text((50, 250), f"Placeholder: {prompt[:40]}", fill=(255, 255, 255))
        return img
    
    def _create_placeholder_depth(self, image: Image.Image) -> np.ndarray:
        """Create placeholder depth when model unavailable"""
        # Use simple edge detection as fallback
        from PIL import ImageFilter
        gray = image.convert('L')
        edges = gray.filter(ImageFilter.FIND_EDGES)
        depth = np.array(edges) / 255.0
        
        # Add gradient
        h, w = depth.shape
        gradient = np.linspace(0, 1, w)
        for i in range(h):
            depth[i, :] = depth[i, :] * 0.5 + gradient * 0.5
        
        return depth


# Global generator instance
_generator = None

def get_generator():
    """Get or initialize generator"""
    global _generator
    if _generator is None:
        print("[INIT] Initializing 3D generator...")
        _generator = ThreeDGenerator()
    return _generator
