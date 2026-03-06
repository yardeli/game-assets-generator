const { useState, useEffect, useRef } = React;

// API Base URL
const API_BASE = "http://127.0.0.1:8001/api";

// Three.js Setup
let scene, camera, renderer, currentModel;

// Wait for THREE to be available
function waitForTHREE() {
    return new Promise((resolve) => {
        if (typeof THREE !== 'undefined') {
            console.log('THREE.js available');
            resolve();
            return;
        }
        
        console.log('Waiting for THREE.js to load...');
        const checkTHREE = setInterval(() => {
            if (typeof THREE !== 'undefined') {
                console.log('THREE.js loaded!');
                clearInterval(checkTHREE);
                resolve();
            }
        }, 100);
        
        // Timeout after 5 seconds
        setTimeout(() => {
            clearInterval(checkTHREE);
            console.error('THREE.js failed to load after 5 seconds');
            resolve(); // Resolve anyway to show placeholder
        }, 5000);
    });
}

async function initThreeJS(containerId) {
    // Make sure THREE is available
    await waitForTHREE();
    
    const container = document.getElementById(containerId);
    if (!container) {
        console.error('Container not found:', containerId);
        return;
    }
    
    console.log('Initializing Three.js for container:', containerId);
    
    if (typeof THREE === 'undefined') {
        console.error('THREE.js not available, cannot initialize');
        return;
    }
    
    try {
        // Scene
        scene = new THREE.Scene();
        scene.background = new THREE.Color(0xf0f0f0);
        
        // Camera
        const width = container.clientWidth || 400;
        const height = container.clientHeight || 400;
        camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
        camera.position.z = 3;
        
        // Renderer
        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(width, height);
        renderer.setPixelRatio(window.devicePixelRatio);
        
        // Clear container and add renderer
        container.innerHTML = '';
        container.appendChild(renderer.domElement);
        
        console.log('Renderer size:', width, 'x', height);
        
        // Lighting
        const light1 = new THREE.DirectionalLight(0xffffff, 0.8);
        light1.position.set(5, 5, 5);
        scene.add(light1);
        
        const light2 = new THREE.AmbientLight(0xffffff, 0.4);
        scene.add(light2);
        
        // Animation loop
        function animate() {
            requestAnimationFrame(animate);
            
            // Rotate model
            if (currentModel) {
                currentModel.rotation.x += 0.005;
                currentModel.rotation.y += 0.01;
            }
            
            renderer.render(scene, camera);
        }
        animate();
        
        console.log('Three.js initialized successfully!');
        
        // Handle window resize
        window.addEventListener('resize', () => {
            const newWidth = container.clientWidth;
            const newHeight = container.clientHeight;
            if (newWidth > 0 && newHeight > 0) {
                camera.aspect = newWidth / newHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(newWidth, newHeight);
            }
        });
    } catch (error) {
        console.error('Error initializing Three.js:', error);
    }
}

function loadModel(modelUrl) {
    if (!scene || !camera || !renderer) {
        console.error('Three.js not initialized');
        return;
    }
    
    if (typeof THREE === 'undefined') {
        console.error('THREE is not defined');
        return;
    }
    
    console.log('Attempting to load model from:', modelUrl);
    
    // Remove old model
    if (currentModel) {
        scene.remove(currentModel);
    }
    
    // Create a placeholder shape while loading
    const geometry = new THREE.BoxGeometry(1, 1, 1);
    const material = new THREE.MeshPhongMaterial({ color: 0x667eea });
    currentModel = new THREE.Mesh(geometry, material);
    scene.add(currentModel);
    
    // Check if GLTFLoader is available
    if (!THREE.GLTFLoader) {
        console.warn('GLTFLoader not available, showing placeholder');
        return;
    }
    
    // Try to load the actual GLB file
    try {
        const loader = new THREE.GLTFLoader();
        loader.load(
            modelUrl,
            (gltf) => {
                console.log('Model loaded successfully!');
                scene.remove(currentModel);
                currentModel = gltf.scene;
                
                // Center and scale model
                const box = new THREE.Box3().setFromObject(currentModel);
                const center = box.getCenter(new THREE.Vector3());
                currentModel.position.sub(center);
                
                const size = box.getSize(new THREE.Vector3());
                const maxDim = Math.max(size.x, size.y, size.z);
                const scale = 2.5 / maxDim;
                currentModel.scale.multiplyScalar(scale);
                
                scene.add(currentModel);
            },
            (progress) => {
                console.log('Loading: ' + ((progress.loaded / progress.total) * 100).toFixed(2) + '%');
            },
            (error) => {
                console.warn('Could not load GLB file, showing placeholder:', error);
                // Keep the placeholder shape visible
            }
        );
    } catch (error) {
        console.error('Error setting up loader:', error);
        // Keep the placeholder shape visible
    }
}

// 3D Model Viewer Component
function ModelViewer({ modelUrl }) {
    useEffect(() => {
        if (!modelUrl) return;
        
        const init = async () => {
            // Wait for container to exist
            let container = document.getElementById('model-viewer');
            let attempts = 0;
            while (!container && attempts < 50) {
                await new Promise(r => setTimeout(r, 100));
                container = document.getElementById('model-viewer');
                attempts++;
            }
            
            if (!container) {
                console.error('Container never appeared');
                return;
            }
            
            console.log('Container found, initializing Three.js...');
            try {
                // Initialize Three.js if not already done
                if (!scene || !renderer) {
                    await initThreeJS('model-viewer');
                }
                
                // Load the model
                if (scene && renderer) {
                    loadModel(modelUrl);
                }
            } catch (error) {
                console.error('Error in ModelViewer:', error);
            }
        };
        
        init();
    }, [modelUrl]);
    
    return null;
}

// Main App Component
function GameAssetsGenerator() {
    const [prompt, setPrompt] = useState("");
    const [style, setStyle] = useState("realistic");
    const [format, setFormat] = useState("glb");
    const [loading, setLoading] = useState(false);
    const [currentGeneration, setCurrentGeneration] = useState(null);
    const [assets, setAssets] = useState([]);
    const [stats, setStats] = useState(null);
    const [styles, setStyles] = useState([]);
    const [formats, setFormats] = useState([]);
    const [activeTab, setActiveTab] = useState("generate");
    const [generationHistory, setGenerationHistory] = useState([]);

    // Load available styles and formats on mount
    useEffect(() => {
        loadStyles();
        loadFormats();
        loadStats();
        loadAssets();
    }, []);

    async function loadStyles() {
        try {
            const response = await fetch(`${API_BASE}/styles`);
            const data = await response.json();
            const stylesList = data.styles || ["realistic", "stylized", "low-poly", "cartoon", "fantasy", "sci-fi"];
            setStyles(stylesList);
        } catch (error) {
            console.error("Error loading styles:", error);
            // Fallback to defaults
            setStyles(["realistic", "stylized", "low-poly", "cartoon", "fantasy", "sci-fi"]);
        }
    }

    async function loadFormats() {
        try {
            const response = await fetch(`${API_BASE}/formats`);
            const data = await response.json();
            const formatsList = Array.isArray(data.formats) 
                ? data.formats.map(f => f.ext || f) 
                : ["glb", "obj", "gltf", "fbx"];
            setFormats(formatsList);
        } catch (error) {
            console.error("Error loading formats:", error);
            // Fallback to defaults
            setFormats(["glb", "obj", "gltf", "fbx"]);
        }
    }

    async function loadStats() {
        try {
            const response = await fetch(`${API_BASE}/stats`);
            const data = await response.json();
            setStats(data);
        } catch (error) {
            console.error("Error loading stats:", error);
        }
    }

    async function loadAssets() {
        try {
            const response = await fetch(`${API_BASE}/assets`);
            const data = await response.json();
            setAssets(data.assets || []);
        } catch (error) {
            console.error("Error loading assets:", error);
        }
    }

    async function generateAsset(e) {
        e.preventDefault();
        
        if (!prompt.trim()) {
            alert("Please enter a prompt!");
            return;
        }

        setLoading(true);
        
        try {
            console.log("Generating asset with prompt:", prompt);
            const response = await fetch(`${API_BASE}/generate`, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify({
                    prompt: prompt,
                    style: style,
                    format: format,
                    user_id: "default"
                })
            });

            console.log("Response status:", response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error("API error:", errorText);
                throw new Error(`API returned ${response.status}: ${errorText}`);
            }

            const data = await response.json();
            console.log("Generation started:", data);
            
            setCurrentGeneration(data);
            setGenerationHistory([data, ...generationHistory].slice(0, 10));
            setPrompt("");
            
            // Poll for completion
            pollGeneration(data.id);
        } catch (error) {
            console.error("Full error:", error);
            alert("Error generating asset: " + error.message);
        } finally {
            setLoading(false);
        }
    }

    async function pollGeneration(generationId) {
        const maxAttempts = 60;
        let attempts = 0;

        const poll = async () => {
            try {
                const response = await fetch(`${API_BASE}/generation/${generationId}`);
                const data = await response.json();
                
                if (data.status === "completed") {
                    setCurrentGeneration({ ...data, complete: true });
                    loadStats();
                } else if (data.status === "failed") {
                    alert("Generation failed!");
                } else if (attempts < maxAttempts) {
                    attempts++;
                    setTimeout(poll, 2000); // Poll every 2 seconds
                } else {
                    alert("Generation timeout");
                }
            } catch (error) {
                console.error("Poll error:", error);
            }
        };

        poll();
    }

    async function saveAsset(generationId) {
        const title = prompt(`Save as (asset name):`);
        if (!title) return;

        try {
            const response = await fetch(`${API_BASE}/assets/${generationId}/save?title=${title}`, {
                method: "POST"
            });

            if (response.ok) {
                alert("Asset saved!");
                loadAssets();
            }
        } catch (error) {
            alert("Error saving asset: " + error.message);
        }
    }

    return (
        <div className="app-container">
            {/* Header */}
            <header className="header">
                <h1>🎮 Game Assets Generator</h1>
                <p>Convert text prompts into production-ready 3D gaming assets</p>
            </header>

            {/* Navigation Tabs */}
            <nav className="tabs">
                <button 
                    className={`tab ${activeTab === "generate" ? "active" : ""}`}
                    onClick={() => setActiveTab("generate")}
                >
                    ✨ Generate
                </button>
                <button 
                    className={`tab ${activeTab === "library" ? "active" : ""}`}
                    onClick={() => setActiveTab("library")}
                >
                    📚 Library
                </button>
                <button 
                    className={`tab ${activeTab === "history" ? "active" : ""}`}
                    onClick={() => setActiveTab("history")}
                >
                    📋 History
                </button>
                <button 
                    className={`tab ${activeTab === "stats" ? "active" : ""}`}
                    onClick={() => setActiveTab("stats")}
                >
                    📊 Stats
                </button>
            </nav>

            {/* Main Content */}
            <main className="main">
                {/* Generate Tab */}
                {activeTab === "generate" && (
                    <section className="section">
                        <div className="generate-layout">
                            {/* Form */}
                            <div className="form-panel">
                                <h2>Create New Asset</h2>
                                
                                <form onSubmit={generateAsset}>
                                    {/* Prompt Input */}
                                    <div className="form-group">
                                        <label htmlFor="prompt">📝 Describe your asset:</label>
                                        <textarea
                                            id="prompt"
                                            value={prompt}
                                            onChange={(e) => setPrompt(e.target.value)}
                                            placeholder="E.g., A wooden sword with a dragon handle, fantasy style, worn leather grip"
                                            rows="4"
                                            disabled={loading}
                                        />
                                    </div>

                                    {/* Style Selection */}
                                    <div className="form-group">
                                        <label htmlFor="style">🎨 Art Style:</label>
                                        <select 
                                            id="style" 
                                            value={style} 
                                            onChange={(e) => setStyle(e.target.value)}
                                            disabled={loading}
                                        >
                                            {styles.length > 0 ? (
                                                styles.map(s => (
                                                    <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                                                ))
                                            ) : (
                                                <option value="">Loading styles...</option>
                                            )}
                                        </select>
                                    </div>

                                    {/* Format Selection */}
                                    <div className="form-group">
                                        <label htmlFor="format">📦 Export Format:</label>
                                        <select 
                                            id="format" 
                                            value={format} 
                                            onChange={(e) => setFormat(e.target.value)}
                                            disabled={loading}
                                        >
                                            <option value="">Select a format...</option>
                                            {formats.map((f, idx) => {
                                                const key = typeof f === 'string' ? f : (f.ext || idx);
                                                const display = typeof f === 'string' ? f.toUpperCase() : f.name;
                                                const value = typeof f === 'string' ? f : f.ext;
                                                return <option key={key} value={value}>{display}</option>;
                                            })}
                                        </select>
                                    </div>

                                    {/* Submit Button */}
                                    <button 
                                        type="submit" 
                                        className="btn-primary"
                                        disabled={loading}
                                    >
                                        {loading ? "Generating..." : "✨ Generate Asset"}
                                    </button>
                                </form>
                            </div>

                            {/* Preview */}
                            <div className="preview-panel">
                                {currentGeneration && currentGeneration.complete ? (
                                    <div className="asset-preview">
                                        <h3>✅ Asset Generated!</h3>
                                        <div id="model-viewer" className="preview-image" style={{width: '100%', height: '400px', display: 'flex', justifyContent: 'center', alignItems: 'center'}} />
                                        <ModelViewer modelUrl={currentGeneration.model_url} />
                                        <div className="asset-info">
                                            <p><strong>Format:</strong> {currentGeneration.format}</p>
                                            <p><strong>Status:</strong> {currentGeneration.status}</p>
                                        </div>
                                        <div className="asset-actions">
                                            <button className="btn-secondary" onClick={() => saveAsset(currentGeneration.id)}>
                                                💾 Save to Library
                                            </button>
                                            <a href={currentGeneration.model_url} download className="btn-secondary">
                                                ⬇️ Download
                                            </a>
                                        </div>
                                    </div>
                                ) : loading ? (
                                    <div className="loading">
                                        <div className="spinner"></div>
                                        <p>🚀 Generating your asset...</p>
                                        <p className="text-secondary">This may take a few moments</p>
                                    </div>
                                ) : (
                                    <div className="placeholder">
                                        <p>📦 Generated assets will appear here</p>
                                        <p className="text-secondary">Enter a prompt and click Generate to create a new asset</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </section>
                )}

                {/* Library Tab */}
                {activeTab === "library" && (
                    <section className="section">
                        <h2>🎮 Asset Library</h2>
                        {assets.length > 0 ? (
                            <div className="asset-grid">
                                {assets.map(asset => (
                                    <div key={asset.id} className="asset-card">
                                        <img src={asset.preview_url} alt={asset.title} />
                                        <h3>{asset.title}</h3>
                                        <p>{asset.format.toUpperCase()}</p>
                                        <a href={asset.url} download className="btn-secondary">
                                            ⬇️ Download
                                        </a>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="empty-state">No saved assets yet. Generate and save some!</p>
                        )}
                    </section>
                )}

                {/* History Tab */}
                {activeTab === "history" && (
                    <section className="section">
                        <h2>📋 Generation History</h2>
                        {generationHistory.length > 0 ? (
                            <div className="history-list">
                                {generationHistory.map(gen => (
                                    <div key={gen.id} className="history-item">
                                        <div className="history-info">
                                            <h4>{gen.prompt}</h4>
                                            <p><strong>Style:</strong> {gen.style}</p>
                                            <p><strong>Status:</strong> <span className={`badge ${gen.status}`}>{gen.status}</span></p>
                                        </div>
                                        {gen.complete && (
                                            <div className="history-actions">
                                                <button className="btn-secondary" onClick={() => saveAsset(gen.id)}>
                                                    💾 Save
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="empty-state">No generation history yet.</p>
                        )}
                    </section>
                )}

                {/* Stats Tab */}
                {activeTab === "stats" && (
                    <section className="section">
                        <h2>📊 Your Statistics</h2>
                        {stats ? (
                            <div className="stats-grid">
                                <div className="stat-card">
                                    <h3>Total Generations</h3>
                                    <p className="stat-value">{stats.total_generations}</p>
                                </div>
                                <div className="stat-card">
                                    <h3>Completed</h3>
                                    <p className="stat-value">{stats.completed}</p>
                                </div>
                                <div className="stat-card">
                                    <h3>Saved Assets</h3>
                                    <p className="stat-value">{stats.saved_assets}</p>
                                </div>
                                <div className="stat-card">
                                    <h3>Success Rate</h3>
                                    <p className="stat-value">{stats.success_rate}%</p>
                                </div>
                            </div>
                        ) : (
                            <p>Loading stats...</p>
                        )}
                    </section>
                )}
            </main>

            {/* Footer */}
            <footer className="footer">
                <p>🎮 Game Assets Generator — Create production-ready 3D assets with AI</p>
            </footer>
        </div>
    );
}

// Render app
ReactDOM.createRoot(document.getElementById('root')).render(<GameAssetsGenerator />);
