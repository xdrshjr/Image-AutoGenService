#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
示例调用脚本 - 演示如何调用图像生成服务API

本脚本展示了如何调用远程图像生成服务的三个主要接口：
1. 根路径：检查服务是否运行
2. 健康检查：检查服务健康状态
3. 图像生成：根据提示词生成图像并保存
"""

import requests
import base64
from PIL import Image
from io import BytesIO
import os
import time
import argparse

# 默认服务器配置（可以通过命令行参数修改）
DEFAULT_SERVER_HOST = "192.168.1.48"  # 这里需要替换为您的服务器IP地址
DEFAULT_SERVER_PORT = 8000  # 根据您的服务配置修改端口号

def check_service_status(base_url):
    """检查服务状态 (根路径)
    
    Args:
        base_url (str): 服务基础URL
        
    Returns:
        dict: 服务状态信息
    """
    print("正在检查服务状态...")
    response = requests.get(f"{base_url}/")
    if response.status_code == 200:
        data = response.json()
        print(f"服务状态: {data}")
        return data
    else:
        print(f"无法连接到服务，状态码: {response.status_code}")
        return None

def check_health(base_url):
    """检查服务健康状态
    
    Args:
        base_url (str): 服务基础URL
        
    Returns:
        dict: 健康状态信息
    """
    print("正在检查服务健康状态...")
    response = requests.get(f"{base_url}/api/health")
    if response.status_code == 200:
        data = response.json()
        print(f"健康状态: {data}")
        return data
    else:
        print(f"健康检查失败，状态码: {response.status_code}")
        return None

def generate_and_save_image(base_url, prompt, seed=None, output_dir="imgs"):
    """生成图像并保存
    
    Args:
        base_url (str): 服务基础URL
        prompt (str): 图像生成提示词
        seed (int, optional): 随机种子，用于复现相同的图像
        output_dir (str, optional): 图像保存目录
        
    Returns:
        str: 保存的图像文件路径，失败则返回None
    """
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 准备请求数据
    request_data = {
        "prompt": prompt
    }
    if seed is not None:
        request_data["seed"] = seed
    
    print(f"正在生成图像，提示词: '{prompt}'...")
    if seed is not None:
        print(f"使用种子: {seed}")
    
    # 发起请求
    try:
        response = requests.post(f"{base_url}/api/generate", json=request_data)
        response.raise_for_status()  # 如果响应状态码不是200，会抛出异常
        
        data = response.json()
        
        # 解码并保存图像
        image_data = base64.b64decode(data["image_base64"])
        image = Image.open(BytesIO(image_data))
        
        # 生成文件名
        timestamp = int(time.time())
        seed_value = data.get("seed", "random")
        filename = f"image_{timestamp}_{seed_value}.png"
        file_path = os.path.join(output_dir, filename)
        
        # 保存图像
        image.save(file_path)
        print(f"图像已保存到: {file_path}")
        
        return file_path
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None
    except Exception as e:
        print(f"处理图像失败: {e}")
        return None

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='图像生成服务API调用示例')
    parser.add_argument('--host', default=DEFAULT_SERVER_HOST, help='服务器主机地址')
    parser.add_argument('--port', type=int, default=DEFAULT_SERVER_PORT, help='服务器端口')
    parser.add_argument('--prompt', default="A cute cat, lay in the bed.", help='图像生成提示词')
    parser.add_argument('--seed', type=int, help='随机种子（可选）')
    parser.add_argument('--output-dir', default="imgs", help='图像保存目录')
    
    args = parser.parse_args()
    
    # 构建基础URL
    base_url = f"http://{args.host}:{args.port}"
    
    print(f"使用服务地址: {base_url}")
    
    # 1. 检查服务状态
    service_status = check_service_status(base_url)
    if not service_status or service_status.get("status") != "running":
        print("服务未运行，退出程序")
        return
    
    # 2. 检查服务健康状态
    health_status = check_health(base_url)
    if not health_status or health_status.get("status") != "ok":
        print("服务健康检查未通过，退出程序")
        return
    
    # 3. 生成并保存图像
    generate_and_save_image(base_url, args.prompt, args.seed, args.output_dir)

if __name__ == "__main__":
    main() 