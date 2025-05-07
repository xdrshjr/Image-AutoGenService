import pytest
from fastapi.testclient import TestClient
import base64
from PIL import Image
from io import BytesIO

from app.main import app


@pytest.fixture
def client():
    """测试客户端"""
    return TestClient(app)


def test_root(client):
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert data["status"] == "running"


def test_health_check(client):
    """测试健康检查接口"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"


def test_generate_image(client):
    """测试图像生成接口
    
    注意：此测试需要加载模型，可能会比较耗时
    """
    # 准备请求数据
    request_data = {
        "prompt": "测试提示词：一只小猫",
        "seed": 42
    }
    
    # 发起请求
    response = client.post("/api/generate", json=request_data)
    
    # 验证响应状态码
    assert response.status_code == 200
    
    # 验证响应数据
    data = response.json()
    assert "image_base64" in data
    assert "prompt" in data
    assert data["prompt"] == request_data["prompt"]
    assert data["seed"] == request_data["seed"]
    
    # 验证图像是否能正确解码
    try:
        image_data = base64.b64decode(data["image_base64"])
        image = Image.open(BytesIO(image_data))
        assert image.size[0] > 0  # 确保图像宽度大于0
        assert image.size[1] > 0  # 确保图像高度大于0
    except Exception as e:
        pytest.fail(f"无法解码图像: {str(e)}") 