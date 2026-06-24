# SynthID Tool

A complete toolkit for detecting and removing SynthID watermarks from AI-generated images. Provides a Python library, CLI tool, REST API, and web interface.

## Features

- **Detection** - Identify SynthID watermarks with confidence scores and phase matching
- **Fast Removal** (V3) - Spectral subtraction that achieves PSNR 43dB+ in seconds
- **Full Removal** (V4) - 7-stage pipeline for maximum watermark suppression
- **Multiple Interfaces** - Python API, CLI, REST API, and drag-and-drop web UI
- **Async Processing** - Queue-ready job pattern for scalable deployments

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/TuyenNedd/reverse-synthid-tool.git
cd reverse-synthid-tool

# Install the package
pip install -e .

# For V4 full pipeline (requires PyTorch)
pip install -e '.[full]'

# For development (includes test dependencies)
pip install -e '.[dev]'
```

### CLI Usage

```bash
# Detect watermark in an image
synthid detect path/to/image.png

# Remove watermark (fast mode - spectral subtraction)
synthid remove input.png output.png --mode fast

# Remove watermark (full mode - 7-stage V4 pipeline)
synthid remove input.png output.png --mode full

# Show help
synthid --help
```

### Python API

```python
from synthid_tool import detect, remove_fast, remove_full

# Detect watermark
result = detect("path/to/image.png")
print(f"Watermarked: {result.is_watermarked}")
print(f"Confidence: {result.confidence:.3f}")

# Fast removal (V3 spectral subtraction)
import numpy as np
from PIL import Image

image = np.array(Image.open("input.png"))
result = remove_fast(image)
Image.fromarray(result.cleaned_image).save("output.png")

# Full removal (V4 7-stage pipeline)
result = remove_full(image)
print(f"PSNR: {result.psnr:.1f} dB")
print(f"Stages applied: {result.stages_applied}")
```

### Web Interface

```bash
# Start the backend API server
uvicorn backend.app:app --reload

# In another terminal, start the frontend dev server
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser. Drag and drop an image to detect or remove watermarks.

### Docker

```bash
# Build and run with docker-compose
docker compose up --build

# Or build manually
docker build -t synthid-tool .
docker run -p 8000:8000 synthid-tool
```

The app will be available at http://localhost:8000 with both the API and web UI served from the same port.

## API Reference

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/detect` | Detect watermark in an uploaded image |
| `POST` | `/api/remove/sync` | Remove watermark synchronously (returns image) |
| `POST` | `/api/remove` | Remove watermark asynchronously (returns job ID) |
| `GET` | `/api/jobs/{id}` | Get job status |
| `GET` | `/api/jobs/{id}/result` | Download job result |
| `GET` | `/api/health` | Health check |

### Detection

```bash
curl -X POST http://localhost:8000/api/detect \
  -F "file=@image.png"
```

Response:
```json
{
  "is_watermarked": true,
  "confidence": 0.847,
  "phase_match": true,
  "details": { ... }
}
```

### Removal (Synchronous)

```bash
curl -X POST http://localhost:8000/api/remove/sync \
  -F "file=@image.png" \
  -F "mode=fast" \
  -o cleaned.png
```

### Removal (Async)

```bash
# Submit job
curl -X POST http://localhost:8000/api/remove \
  -F "file=@image.png" \
  -F "mode=full"
# Returns: {"job_id": "abc-123", "status": "pending"}

# Poll status
curl http://localhost:8000/api/jobs/abc-123
# Returns: {"job_id": "abc-123", "status": "completed"}

# Download result
curl http://localhost:8000/api/jobs/abc-123/result -o cleaned.png
```

### Swagger UI

Interactive API documentation is available at http://localhost:8000/docs when the server is running.

## Architecture

```
reverse-synthid-tool/
├── src/synthid_tool/          # Core Python library
│   ├── __init__.py            # Public API: detect(), remove_fast(), remove_full()
│   ├── detector.py            # Detection logic
│   ├── remover.py             # Removal orchestration (V3 + V4)
│   ├── codebook.py            # Thread-safe lazy codebook loading
│   ├── models.py              # Result dataclasses
│   ├── config.py              # Configuration with env var overrides
│   ├── cli.py                 # Typer CLI entry point
│   └── _engine/               # Adapted core algorithms
│       ├── robust_extractor.py
│       ├── synthid_bypass.py
│       ├── synthid_bypass_v4.py
│       ├── vae_regen.py
│       └── watermark_remover.py
├── backend/                   # FastAPI REST API
│   ├── app.py                 # App factory + CORS + lifespan
│   ├── config.py              # Server configuration
│   ├── job_store.py           # In-memory async job store
│   ├── services.py            # Business logic layer
│   └── routes/
│       ├── detect.py          # POST /api/detect
│       ├── remove.py          # POST /api/remove, /api/remove/sync
│       └── jobs.py            # GET /api/jobs/{id}
├── frontend/                  # React + Vite + TypeScript + Tailwind
│   └── src/
│       ├── App.tsx
│       ├── components/
│       │   ├── ImageDropzone.tsx
│       │   ├── DetectionResult.tsx
│       │   ├── RemovalPanel.tsx
│       │   ├── ImageComparison.tsx
│       │   └── Header.tsx
│       └── api/client.ts
├── artifacts/                 # Pre-trained codebooks
│   ├── spectral_codebook_v3.npz
│   ├── spectral_codebook_v4.npz
│   └── codebook/robust_codebook.pkl
├── tests/                     # pytest test suite (46 tests)
├── Dockerfile                 # Multi-stage production build
├── docker-compose.yml         # Local development setup
└── pyproject.toml             # Python package configuration
```

### Processing Modes

**Fast Mode (V3)** - Spectral codebook subtraction
- Analyzes frequency-domain watermark carriers
- Subtracts estimated watermark signal
- Achieves PSNR 43dB+ with minimal visual impact
- Completes in seconds

**Full Mode (V4)** - 7-stage pipeline
- Multi-round spectral analysis and suppression
- Phase-aware filtering
- VAE regeneration for stubborn patterns
- Maximum watermark removal
- Requires PyTorch (`pip install -e '.[full]'`)

## Configuration

Environment variables for customization:

| Variable | Default | Description |
|----------|---------|-------------|
| `SYNTHID_ARTIFACTS_DIR` | `./artifacts` | Path to codebook files |
| `SYNTHID_HOST` | `0.0.0.0` | Server bind address |
| `SYNTHID_PORT` | `8000` | Server port |
| `SYNTHID_MAX_UPLOAD_SIZE` | `52428800` | Max upload size in bytes (50 MB) |
| `SYNTHID_RESULTS_DIR` | `./.results` | Directory for async job results |
| `SYNTHID_DEFAULT_MODEL` | (none) | Default model for V4 full mode |

## Development

### Prerequisites

- Python 3.9+
- Node.js 20+
- npm

### Setup

```bash
# Install Python package in dev mode
pip install -e '.[dev]'

# Install frontend dependencies
cd frontend && npm install && cd ..

# Run tests
pytest tests/ -v

# Run backend (auto-reload)
uvicorn backend.app:app --reload

# Run frontend dev server (separate terminal)
cd frontend && npm run dev
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=synthid_tool --cov=backend

# Specific test file
pytest tests/test_core.py -v
pytest tests/test_backend.py -v
pytest tests/test_cli.py -v
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes and add tests
4. Run the test suite (`pytest tests/ -v`)
5. Commit your changes (`git commit -m 'feat: add your feature'`)
6. Push to the branch (`git push origin feature/your-feature`)
7. Open a Pull Request

### Commit Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `chore:` - Maintenance tasks
- `refactor:` - Code refactoring
- `test:` - Test additions or changes

## License

MIT
