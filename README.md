# AI图像生成服务

这是一个基于FLUX模型的AI图像生成后台服务，提供REST API接口生成图像。

## 特性

- 基于FastAPI构建的高性能REST API
- 支持FLUX模型及LORA模型加载
- 通过配置文件动态配置服务参数
- 一键启动脚本支持（Windows和Linux/macOS）
- 提供API测试和健康检查

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

#### 示例请求（使用curl）

```bash
curl -X POST "http://localhost:8000/api/generate" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "一只小猫坐在窗台上", "seed": 42}'
```

#### 响应示例

```json
{
  "image_base64": "...(base64编码的图像数据)...",
  "file_path": "./output/images/20230501_120000.jpg",
  "prompt": "一只小猫坐在窗台上",
  "seed": 42,
  "timestamp": "20230501_120000"
}
```

## 运行测试

使用pytest运行测试：

```bash
pytest
```

## 许可证

MIT 