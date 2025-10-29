#!/bin/bash
set -euo pipefail

# 准备运行目录
mkdir -p ./logs ./data

# 使用 Uvicorn 启动 Django ASGI 应用
python manage.py makemigrations
python manage.py migrate

# 运行 Uvicorn（前台运行，便于容器管理和信号传递）
: "${HOST:=0.0.0.0}"
: "${PORT:=21114}"
: "${WORKERS:=4}"

echo "正在启动 Uvicorn (workers=${WORKERS})..."
exec python -m uvicorn rustdesk_api.asgi:application \
  --host "${HOST}" \
  --port "${PORT}" \
  --workers "${WORKERS}" \
  --proxy-headers
