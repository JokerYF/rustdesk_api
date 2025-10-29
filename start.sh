#!/bin/bash
set -euo pipefail

# 准备运行目录
mkdir -p ./logs ./data

# 使用uWSGI启动Django应用
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# 如果存在遗留的 uWSGI pid 文件，先清理
if [ -f ./uwsgi.pid ]; then
    echo "停止现有的uWSGI实例..."
    kill -TERM "$(cat ./uwsgi.pid)" || true
    rm -f ./uwsgi.pid
fi

# 启动uWSGI（前台运行，便于容器管理和信号传递）
echo "正在启动uWSGI..."
exec uwsgi --ini uwsgi.ini
