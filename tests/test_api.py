import pytest
import requests
import base64
from PIL import Image
from io import BytesIO
import os
import time

# 远程服务器配置
SERVER_HOST = "192.168.1.48"  # 这里需要替换为您的Ubuntu服务器IP地址
SERVER_PORT = 8000  # 根据您的服务配置修改端口号
BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

# 不再使用TestClient
# from app.main import app
# @pytest.fixture
# def client():
#     """测试客户端"""
#     return TestClient(app)


def test_root():
    """测试根路径"""
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert data["status"] == "running"


def test_health_check():
    """测试健康检查接口"""
    response = requests.get(f"{BASE_URL}/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"


def test_generate_image():
    """测试图像生成接口并保存图片
    
    注意：该测试调用远程服务器的图像生成API，并将生成的图片保存到imgs目录下
    """
    # 确保imgs目录存在
    imgs_dir = os.path.join(os.getcwd(), "imgs")
    if not os.path.exists(imgs_dir):
        os.makedirs(imgs_dir)
    
    # 准备请求数据
    request_data = {
        "prompt": "A cute cat, lay in the bed.",
        "seed": 42
    }
    
    # 发起请求到远程服务器
    response = requests.post(f"{BASE_URL}/api/generate", json=request_data)
    
    # 验证响应状态码
    assert response.status_code == 200
    
    # 验证响应数据
    data = response.json()
    assert "image_base64" in data
    assert "prompt" in data
    assert data["prompt"] == request_data["prompt"]
    assert data["seed"] == request_data["seed"]
    
    # 验证图像是否能正确解码并保存
    try:
        image_data = base64.b64decode(data["image_base64"])
        image = Image.open(BytesIO(image_data))
        assert image.size[0] > 0  # 确保图像宽度大于0
        assert image.size[1] > 0  # 确保图像高度大于0
        
        # 生成文件名并保存图片
        timestamp = int(time.time())
        filename = f"image_{timestamp}_{request_data['seed']}.png"
        file_path = os.path.join(imgs_dir, filename)
        image.save(file_path)
        
        # 验证文件是否成功保存
        assert os.path.exists(file_path)
        print(f"图片已保存到: {file_path}")
    except Exception as e:
        pytest.fail(f"无法处理或保存图像: {str(e)}") 