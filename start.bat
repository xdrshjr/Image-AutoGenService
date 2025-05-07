@echo off
echo 设置环境变量...
set PYTHONPATH=%PYTHONPATH%;%cd%

echo 创建输出目录...
if not exist "output\images" mkdir output\images

echo 检查是否已安装依赖...
if not exist "venv" (
    echo 正在创建虚拟环境...
    python -m venv venv
    
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
    
    echo 正在安装依赖...
    pip install -r requirements.txt
) else (
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
)

echo 正在启动图像生成服务...
for /f "tokens=*" %%a in ('python -c "import yaml; config = yaml.safe_load(open('config.yaml')); print(config['server']['host'] + ':' + str(config['server']['port']))"') do set CONFIG=%%a
echo 使用配置: %CONFIG%

uvicorn app.main:app --host 0.0.0.0 --port 8000

pause 