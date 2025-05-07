import pytest
import requests
import base64
from PIL import Image
from io import BytesIO
import os
import time
import json

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


@pytest.fixture(scope="session", autouse=True)
def cleanup_temp_files():
    """测试会话结束后清理临时文件"""
    yield  # 测试执行
    # 测试结束后清理
    temp_file = "temp_task_id.txt"
    if os.path.exists(temp_file):
        os.remove(temp_file)
        print(f"已删除临时文件: {temp_file}")


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


def test_async_image_generation():
    """测试异步图像生成流程
    
    这个测试会测试创建异步生成任务的过程，并返回任务ID
    """
    # 准备请求数据
    request_data = {
        "prompt": "A beautiful landscape with mountains and a lake",
        "seed": 123
    }
    
    # 创建异步生成任务
    response = requests.post(f"{BASE_URL}/api/generate-async", json=request_data)
    assert response.status_code == 200
    task_data = response.json()
    assert "task_id" in task_data
    assert "status" in task_data
    
    task_id = task_data["task_id"]
    print(f"已创建异步任务: {task_id}")
    
    # 将任务ID写入临时文件，供其他测试使用
    with open("temp_task_id.txt", "w") as f:
        f.write(task_id)
    
    # 返回任务ID以便后续测试使用
    return task_id


def test_task_progress_and_download():
    """测试任务进度查询和图片下载
    
    这个测试会测试以下流程：
    1. 读取之前创建的任务ID或从接口获取最新的任务ID
    2. 轮询任务状态直到完成
    3. 获取并保存生成的图片
    """
    # 确保imgs目录存在
    imgs_dir = os.path.join(os.getcwd(), "imgs")
    if not os.path.exists(imgs_dir):
        os.makedirs(imgs_dir)
    
    # 尝试读取之前创建的任务ID
    task_id = None
    try:
        with open("temp_task_id.txt", "r") as f:
            task_id = f.read().strip()
        print(f"使用之前创建的任务ID: {task_id}")
    except FileNotFoundError:
        # 如果找不到文件，则从任务列表中获取最新的任务ID
        response = requests.get(f"{BASE_URL}/api/tasks")
        if response.status_code == 200:
            tasks = response.json().get("tasks", [])
            if tasks:
                task_id = tasks[0].get("id")
                print(f"使用最新的任务ID: {task_id}")
    
    # 确保有有效的任务ID
    if not task_id:
        pytest.skip("没有可用的任务ID，跳过测试")
    
    # 轮询任务状态
    max_polls = 30  # 最大轮询次数
    poll_interval = 2  # 轮询间隔（秒）
    
    progress_log = []
    for i in range(max_polls):
        response = requests.get(f"{BASE_URL}/api/task/{task_id}")
        assert response.status_code == 200
        status_data = response.json()
        
        # 记录进度
        progress_info = f"进度: {status_data['progress']}/{status_data['total_steps']} ({(status_data['progress']/max(1, status_data['total_steps'])*100):.1f}%)"
        if not progress_log or progress_log[-1] != progress_info:
            progress_log.append(progress_info)
            print(progress_info)
        
        # 检查任务是否已完成或失败
        if status_data["status"] in ["completed", "failed"]:
            print(f"任务状态: {status_data['status']}")
            if status_data["status"] == "failed" and status_data.get("error"):
                print(f"错误信息: {status_data['error']}")
            break
            
        time.sleep(poll_interval)
    else:
        pytest.fail("任务在最大轮询次数内未完成")
    
    # 打印进度日志
    print(f"进度更新次数: {len(progress_log)}")
    
    # 获取生成结果
    response = requests.get(f"{BASE_URL}/api/result/{task_id}")
    assert response.status_code == 200
    result_data = response.json()
    
    # 验证结果
    assert "image_base64" in result_data
    assert "prompt" in result_data
    
    # 保存图像
    try:
        image_data = base64.b64decode(result_data["image_base64"])
        image = Image.open(BytesIO(image_data))
        assert image.size[0] > 0
        assert image.size[1] > 0
        
        # 生成文件名并保存
        timestamp = int(time.time())
        seed = result_data.get("seed", 0)
        filename = f"async_image_{timestamp}_{seed}.png"
        file_path = os.path.join(imgs_dir, filename)
        image.save(file_path)
        
        # 验证保存成功
        assert os.path.exists(file_path)
        print(f"异步生成的图片已保存到: {file_path}")
    except Exception as e:
        pytest.fail(f"无法处理或保存异步生成的图像: {str(e)}")


def test_list_tasks():
    """测试任务列表接口"""
    response = requests.get(f"{BASE_URL}/api/tasks")
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert isinstance(data["tasks"], list)
    
    # 打印任务列表
    if data["tasks"]:
        print(f"找到 {len(data['tasks'])} 个任务:")
        for task in data["tasks"]:
            status = task.get("status", "unknown")
            prompt = task.get("prompt", "无提示词")
            created_at = task.get("created_at", "未知时间")
            print(f"- ID: {task.get('id')}, 状态: {status}, 提示词: {prompt}, 创建时间: {created_at}")
    else:
        print("任务列表为空")


# 用于直接运行此文件时的主函数
if __name__ == "__main__":
    import sys
    
    # 默认测试
    test_to_run = "all"
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        test_to_run = sys.argv[1].lower()
    
    # 测试映射
    test_map = {
        "root": test_root,
        "health": test_health_check,
        "generate": test_generate_image,
        "async": test_async_image_generation,
        "progress": test_task_progress_and_download,
        "list": test_list_tasks
    }
    
    if test_to_run == "all":
        print("执行所有测试...")
        # 按顺序执行所有测试
        test_root()
        test_health_check()
        task_id = test_async_image_generation()
        print(f"等待5秒后检查任务进度...")
        time.sleep(5)  # 给一些时间让任务开始处理
        test_task_progress_and_download()
        test_list_tasks()
    elif test_to_run in test_map:
        print(f"执行测试: {test_to_run}")
        test_map[test_to_run]()
    else:
        print(f"未知测试: {test_to_run}")
        print(f"可用的测试: {', '.join(test_map.keys())}, all")
        sys.exit(1)
        
    print("测试完成!") 