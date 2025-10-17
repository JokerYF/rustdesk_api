# 使用Python官方镜像作为基础镜像
FROM python:3.13-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制项目代码
COPY . /app

# 设置工作目录
WORKDIR /app

RUN pip install uv && uv sync

# 创建日志目录和.env文件
RUN if [ ! -f .env ]; then touch .env; fi

# 设置权限
RUN chmod +x start.sh

# 暴露端口
EXPOSE 21114

# 设置环境变量
ENV ENV_FILE=.env

# 启动应用
CMD ["./start.sh"]