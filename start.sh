#!/bin/bash

# 使用uWSGI启动Django应用

source .venv/bin/activate

python manage.py migrate

# 检查是否已经有一个uWSGI实例在运行
if [ -f ./uwsgi.pid ]; then
    echo "停止现有的uWSGI实例..."
    kill -TERM $(cat ./uwsgi.pid)
    rm -f ./uwsgi.pid
fi

# 启动uWSGI
echo "正在启动uWSGI..."
uwsgi --ini uwsgi.ini &
