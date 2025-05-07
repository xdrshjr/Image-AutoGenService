# OneClickFluxGen

A high-performance AI image generation backend service based on the FLUX model, providing REST API interfaces for image generation.

## Features

- High-performance REST API built with FastAPI
- Support for FLUX model and LORA model loading
- Dynamic service configuration via configuration file
- One-click startup scripts for Windows and Linux/macOS
- API testing and health check endpoints
- Both synchronous and asynchronous image generation
- Task management with progress tracking

## System Requirements

- Python 3.8+
- PyTorch 2.0+
- CUDA support (optional, for GPU acceleration)

## Quick Start

### 1. Configuration

Edit the `config.yaml` file to configure server address, port, and model paths:

```yaml
server:
  host: "0.0.0.0"  # Listen on all network interfaces
  port: 8000        # Service port

model:
  model_id: "/path/to/your/model"  # Replace with your model path
  use_lora: false
  # LORA configuration (optional)
  lora:
    lora_dir: "output/your_lora_dir"
    weight_name: "your_lora_name.safetensors"
  
  # Inference parameters
  num_inference_steps: 23
  use_cpu_offload: true
  output_dir: "./output/images"
```

### 2. Starting the Service

#### Windows:

Run the `start.bat` batch file:

```
start.bat
```

#### Linux/macOS:

Run the `start.sh` script (grant execute permission first):

```
chmod +x start.sh
./start.sh
```

### 3. Using the API

After the service starts, you can access the API through:

- API documentation: http://localhost:8000/docs
- Image generation API: `POST /api/generate`
- Health check API: `GET /api/health`

## API Usage Examples

### Example Client

The repository includes an example client (`example_call.py`) that demonstrates how to use all API endpoints. You can run it with various options:

```bash
# Basic synchronous image generation
python example_call.py --host 127.0.0.1 --port 8000 --prompt "A cute cat, lay in the bed." --mode sync

# Asynchronous image generation workflow (create, wait, download)
python example_call.py --prompt "A beautiful landscape with mountains" --mode workflow

# List all tasks
python example_call.py --mode list

# Check status of a specific task
python example_call.py --mode status --task-id <task_id>

# Get result of a completed task
python example_call.py --mode result --task-id <task_id>
```

### Command-line Options for example_call.py

| Option | Description |
|--------|-------------|
| `--host` | Server host address (default: 127.0.0.1) |
| `--port` | Server port (default: 8000) |
| `--prompt` | Image generation prompt (default: "A cute cat, lay in the bed.") |
| `--seed` | Random seed for reproducibility (optional) |
| `--output-dir` | Directory to save images (default: "imgs") |
| `--mode` | Operation mode: sync, async, status, result, list, workflow (default: sync) |
| `--task-id` | Task ID for status/result operations (optional) |

### Using cURL

#### Generate an image (synchronous)

```bash
curl -X POST "http://localhost:8000/api/generate" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "A small kitten sitting on a window sill", "seed": 42}'
```

Response:
```json
{
  "image_base64": "...(base64 encoded image data)...",
  "file_path": "./output/images/20230501_120000.jpg",
  "prompt": "A small kitten sitting on a window sill",
  "seed": 42,
  "timestamp": "20230501_120000"
}
```

#### Create an asynchronous generation task

```bash
curl -X POST "http://localhost:8000/api/generate-async" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "A beautiful landscape with mountains and a lake", "seed": 123}'
```

Response:
```json
{
  "task_id": "task_1234567890",
  "status": "pending"
}
```

#### Check task status

```bash
curl -X GET "http://localhost:8000/api/task/task_1234567890"
```

Response:
```json
{
  "task_id": "task_1234567890",
  "status": "in_progress",
  "progress": 15,
  "total_steps": 23,
  "created_at": "2023-05-01T12:00:00"
}
```

#### Get task result

```bash
curl -X GET "http://localhost:8000/api/result/task_1234567890"
```

Response:
```json
{
  "image_base64": "...(base64 encoded image data)...",
  "prompt": "A beautiful landscape with mountains and a lake",
  "seed": 123
}
```

#### List all tasks

```bash
curl -X GET "http://localhost:8000/api/tasks"
```

Response:
```json
{
  "tasks": [
    {
      "id": "task_1234567890",
      "status": "completed",
      "prompt": "A beautiful landscape with mountains and a lake",
      "created_at": "2023-05-01T12:00:00"
    },
    {
      "id": "task_0987654321",
      "status": "pending",
      "prompt": "A futuristic city with flying cars",
      "created_at": "2023-05-01T12:05:00"
    }
  ]
}
```

## Running Tests

Use pytest to run tests:

```bash
pytest
```

For a specific test:

```bash
# Run only the synchronous image generation test
pytest tests/test_api.py::test_generate_image

# Run only the asynchronous workflow test
pytest tests/test_api.py::test_async_image_generation tests/test_api.py::test_task_progress_and_download
```

## License

MIT 