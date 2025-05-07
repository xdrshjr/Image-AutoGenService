#!/bin/bash

# 设置环境变量
export PYTHONPATH=$PYTHONPATH:$(pwd)

# 创建输出目录
mkdir -p ./output/images

# 检查是否已安装依赖
if [ ! -d "venv" ]; then
    echo "正在创建虚拟环境..."
    python -m venv venv
    
    # 激活虚拟环境
    source venv/bin/activate
    
    echo "正在安装依赖..."
    pip install -r requirements.txt
else
    # 激活虚拟环境
    source venv/bin/activate
fi

# 启动服务
echo "正在启动图像生成服务..."
uvicorn app.main:app --host $(grep -A 2 'server:' config.yaml | grep 'host' | awk '{print $2}' | tr -d '"') --port $(grep -A 3 'server:' config.yaml | grep 'port' | awk '{print $2}') 