import os
import yaml
from pydantic import BaseModel
from typing import Dict, Any, Optional


class LoraConfig(BaseModel):
    lora_dir: str
    weight_name: str


class ModelConfig(BaseModel):
    model_id: str
    use_lora: bool
    lora: Optional[LoraConfig] = None
    num_inference_steps: int = 23
    use_cpu_offload: bool = True
    output_dir: str = "./output/images"


class ServerConfig(BaseModel):
    host: str
    port: int


class AppConfig(BaseModel):
    server: ServerConfig
    model: ModelConfig


def load_config(config_path: str = "config.yaml") -> AppConfig:
    """从YAML文件加载配置"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)
    
    return AppConfig(**config_data)


# 全局配置实例
config = load_config() 