# 使用Python官方镜像作为基础镜像
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 安装构建依赖
#RUN apt-get update && apt-get install -y \
#    gcc \
#    && rm -rf /var/lib/apt/lists/*

# 复制项目代码
COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

EXPOSE 21114

VOLUME ["/app/logs", "/app/data"]

RUN chmod +x start.sh

CMD ["./start.sh"]