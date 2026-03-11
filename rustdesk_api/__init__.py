# 在 Django 启动时记录当前环境变量
from common.runtime_config_logger import log_current_env_vars

# 记录当前环境变量到 runtime_config.json 文件
log_current_env_vars()
