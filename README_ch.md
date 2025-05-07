# AI图像生成服务

基于FLUX模型的高性能AI图像生成后台服务，提供REST API接口生成图像。

## 特性

- 基于FastAPI构建的高性能REST API
- 支持FLUX模型及LORA模型加载
- 通过配置文件动态配置服务参数
- 一键启动脚本支持（Windows和Linux/macOS）
- 提供API测试和健康检查
- 支持同步和异步图像生成
- 任务管理与进度追踪

## 运行环境要求

- Python 3.8+
- PyTorch 2.0+
- CUDA支持（可选，用于GPU加速）

## 快速开始

### 1. 配置

编辑`config.yaml`文件，配置服务器地址、端口和模型路径：

```yaml
server:
  host: "0.0.0.0"  # 监听所有网络接口
  port: 8000        # 服务端口

model:
  model_id: "/path/to/your/model"  # 修改为您的模型路径
  use_lora: false
  # LORA配置（可选）
  lora:
    lora_dir: "output/your_lora_dir"
    weight_name: "your_lora_name.safetensors"
  
  # 推理参数
  num_inference_steps: 23
  use_cpu_offload: true
  output_dir: "./output/images"
```

### 2. 启动服务

#### Windows:

运行`start.bat`批处理文件：

```
start.bat
```

#### Linux/macOS:

运行`start.sh`脚本（需要先授予执行权限）：

```
chmod +x start.sh
./start.sh
```

### 3. 使用API

服务启动后，可以通过以下方式访问API：

- API文档：http://localhost:8000/docs
- 生成图像API：`POST /api/generate`
- 健康检查API：`GET /api/health`

## API使用示例

### 示例客户端

仓库中包含一个示例客户端 (`example_call.py`)，演示如何使用所有API端点。您可以使用各种选项运行它：

```bash
# 基本的同步图像生成
python example_call.py --host 127.0.0.1 --port 8000 --prompt "一只可爱的猫咪躺在床上" --mode sync

# 异步图像生成工作流（创建、等待、下载）
python example_call.py --prompt "一个美丽的山水风景" --mode workflow

# 列出所有任务
python example_call.py --mode list

# 检查特定任务的状态
python example_call.py --mode status --task-id <任务ID>

# 获取已完成任务的结果
python example_call.py --mode result --task-id <任务ID>
```

### example_call.py 的命令行选项

| 选项 | 描述 |
|--------|-------------|
| `--host` | 服务器主机地址（默认：127.0.0.1） |
| `--port` | 服务器端口（默认：8000） |
| `--prompt` | 图像生成提示词（默认："A cute cat, lay in the bed."） |
| `--seed` | 随机种子，用于复现相同的图像（可选） |
| `--output-dir` | 保存图像的目录（默认："imgs"） |
| `--mode` | 操作模式：sync（同步），async（异步），status（状态），result（结果），list（列表），workflow（工作流）（默认：sync） |
| `--task-id` | 用于状态/结果操作的任务ID（可选） |

### 使用cURL

#### 生成图像（同步）

```bash
curl -X POST "http://localhost:8000/api/generate" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "一只小猫坐在窗台上", "seed": 42}'
```

响应示例：
```json
{
  "image_base64": "...(base64编码的图像数据)...",
  "file_path": "./output/images/20230501_120000.jpg",
  "prompt": "一只小猫坐在窗台上",
  "seed": 42,
  "timestamp": "20230501_120000"
}
```

#### 创建异步生成任务

```bash
curl -X POST "http://localhost:8000/api/generate-async" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "一个美丽的山水湖泊风景", "seed": 123}'
```

响应示例：
```json
{
  "task_id": "task_1234567890",
  "status": "pending"
}
```

#### 检查任务状态

```bash
curl -X GET "http://localhost:8000/api/task/task_1234567890"
```

响应示例：
```json
{
  "task_id": "task_1234567890",
  "status": "in_progress",
  "progress": 15,
  "total_steps": 23,
  "created_at": "2023-05-01T12:00:00"
}
```

#### 获取任务结果

```bash
curl -X GET "http://localhost:8000/api/result/task_1234567890"
```

响应示例：
```json
{
  "image_base64": "...(base64编码的图像数据)...",
  "prompt": "一个美丽的山水湖泊风景",
  "seed": 123
}
```

#### 列出所有任务

```bash
curl -X GET "http://localhost:8000/api/tasks"
```

响应示例：
```json
{
  "tasks": [
    {
      "id": "task_1234567890",
      "status": "completed",
      "prompt": "一个美丽的山水湖泊风景",
      "created_at": "2023-05-01T12:00:00"
    },
    {
      "id": "task_0987654321",
      "status": "pending",
      "prompt": "未来城市与飞行汽车",
      "created_at": "2023-05-01T12:05:00"
    }
  ]
}
```

## 运行测试

使用pytest运行测试：

```bash
pytest
```

运行特定测试：

```bash
# 仅运行同步图像生成测试
pytest tests/test_api.py::test_generate_image

# 仅运行异步工作流测试
pytest tests/test_api.py::test_async_image_generation tests/test_api.py::test_task_progress_and_download
```

## 许可证

MIT 