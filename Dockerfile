# 使用Python官方镜像作为基础镜像
FROM docker.1ms.run/python:3.13-slim

ARG APP_VERSION
RUN if [ -n "$APP_VERSION" ]; then \
    printf '%s' "$APP_VERSION" > /app/version; \
    fi

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV APP_VERSION=${APP_VERSION}

# 复制项目代码
COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

EXPOSE 21114

VOLUME ["/app/logs", "/app/data"]

RUN chmod +x start.sh


CMD ["./start.sh"]