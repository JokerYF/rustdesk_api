# ---- Stage 1: 前端混淆 ----
FROM docker.1ms.run/node:20-alpine AS frontend

WORKDIR /build
COPY static/ ./static/
COPY obfuscate.js ./

RUN npm install --no-fund --no-audit javascript-obfuscator cssnano postcss \
    && node obfuscate.js

# ---- Stage 2: Python 应用 ----
FROM docker.1ms.run/python:3.13-slim

ARG APP_VERSION

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

COPY . .
COPY --from=frontend /build/output/ ./static/

RUN rm -f obfuscate.js \
    && if [ -n "$APP_VERSION" ]; then printf '%s' "$APP_VERSION" > ./version; fi \
    && python manage.py collectstatic --noinput \
    && chmod +x start.sh

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    APP_VERSION=${APP_VERSION}

EXPOSE 21114

VOLUME ["/app/logs", "/app/data"]

CMD ["./start.sh"]
