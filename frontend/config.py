# 配置管理模块
import os

# 环境配置
ENVIRONMENTS = {
    "local": {
        "api_base_url": "http://localhost:8000",
        "name": "本地环境"
    },
    "production": {
        "api_base_url": "https://ecommerce-behavior-api-production.up.railway.app",
        "name": "线上环境"
    }
}

# 从环境变量获取当前环境
def get_current_environment():
    """获取当前环境"""
    env = os.getenv("APP_ENV", "local")
    return env

# 获取API基础URL
def get_api_base_url():
    """获取API基础URL"""
    # 优先从环境变量获取（最高优先级）
    api_url = os.getenv("API_BASE_URL")
    if api_url:
        return api_url
    
    # 从配置中获取
    env = get_current_environment()
    return ENVIRONMENTS.get(env, ENVIRONMENTS["local"])["api_base_url"]

# 获取所有环境配置
def get_all_environments():
    """获取所有环境配置"""
    return ENVIRONMENTS
