<div align="center">

# RustDesk API Server

[English](./README_EN.md) | 中文

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Django Version](https://img.shields.io/badge/django-5.2-green.svg)](https://www.djangoproject.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

一个功能完善的 RustDesk API 服务器，提供客户端认证、设备管理、地址簿管理、审计日志等功能。

</div>

---

## 📖 目录

- [特性](#特性)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
  - [环境要求](#环境要求)
  - [Docker 部署（推荐）](#docker-部署推荐)
  - [手动部署](#手动部署)
- [配置说明](#配置说明)
- [API 文档](#api-文档)
  - [客户端 API](#客户端-api)
  - [Web 管理 API](#web-管理-api)
- [数据库模型](#数据库模型)
- [开发指南](#开发指南)
- [常见问题](#常见问题)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## ✨ 特性

### 核心功能

- 🔐 **用户认证系统** - 支持用户注册、登录、令牌管理
- 💓 **心跳检测** - 实时监控客户端在线状态
- 📊 **系统信息收集** - 自动收集并存储客户端系统信息
- 🏷️ **设备标签管理** - 支持设备分组和标签管理
- 📒 **地址簿管理** - 支持个人和共享地址簿
- 📝 **审计日志** - 记录连接和文件传输日志
- 🌐 **多语言支持** - 支持中文和英文界面
- 🎨 **Web 管理界面** - 提供友好的 Web 管理后台

### 技术特性

- 🚀 **高性能** - 基于 Django + Gunicorn，支持多进程多线程
- 🐳 **容器化部署** - 完整的 Docker 支持
- 💾 **多数据库支持** - 支持 SQLite、MySQL、PostgreSQL
- 🔧 **灵活配置** - 通过环境变量轻松配置
- 📱 **跨平台** - 支持 Windows、macOS、Linux

## 🏗️ 系统架构

```
rustdesk_api/
├── apps/
│   ├── client_apis/      # 客户端 API 接口
│   │   ├── views.py      # 核心 API 视图
│   │   ├── view_ab.py    # 地址簿 API
│   │   └── view_audit.py # 审计日志 API
│   ├── web/              # Web 管理界面
│   │   ├── view_auth.py  # 认证视图
│   │   ├── view_home.py  # 主页视图
│   │   ├── view_user.py  # 用户管理
│   │   └── view_personal.py # 地址簿管理
│   ├── db/               # 数据库模型和服务
│   │   ├── models.py     # 数据模型定义
│   │   └── service.py    # 数据库服务层
│   ├── commands/         # 管理命令
│   └── common/           # 公共中间件
├── common/               # 公共工具
│   ├── db_config.py      # 数据库配置
│   ├── env.py            # 环境变量管理
│   ├── logging_config.py # 日志配置
│   └── utils.py          # 工具函数
├── static/               # 静态文件
├── templates/            # 模板文件
└── rustdesk_api/         # Django 项目配置
```

## 🚀 快速开始

### 环境要求

- Python 3.13+
- Docker & Docker Compose（容器化部署）
- SQLite / MySQL / PostgreSQL（数据库）

### Docker 部署（推荐）

1. **克隆项目**

```bash
git clone https://github.com/yourusername/rustdesk_api.git
cd rustdesk_api
```

2. **启动服务**

```bash
docker-compose up -d
```

3. **访问服务**

- API 服务: `http://localhost:21114`
- Web 管理: `http://localhost:21114/web/`

服务将自动完成数据库迁移和初始化。

### 手动部署

1. **克隆项目**

```bash
git clone https://github.com/yourusername/rustdesk_api.git
cd rustdesk_api
```

2. **创建虚拟环境**

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **配置环境变量**

```bash
# 创建 .env 文件或设置环境变量
export DATABASE=sqlite3
export DEBUG=False
export WORKERS=4
export THREADS=8
```

5. **数据库迁移**

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

6. **创建管理员账户**

```bash
python manage.py createsuperuser
```

7. **启动服务**

```bash
# 开发环境
python manage.py runserver 0.0.0.0:21114

# 生产环境
./start.sh
```

## ⚙️ 配置说明

### 环境变量

| 变量名               | 说明           | 默认值             | 可选值                              |
|-------------------|--------------|-----------------|----------------------------------|
| `DATABASE`        | 数据库类型        | `sqlite3`       | `sqlite3`, `mysql`, `postgresql` |
| `DEBUG`           | 调试模式         | `False`         | `True`, `False`                  |
| `HOST`            | 监听地址         | `0.0.0.0`       | 任何有效 IP                          |
| `PORT`            | 监听端口         | `21114`         | 1-65535                          |
| `WORKERS`         | Gunicorn 进程数 | `4`             | 建议 2-8                           |
| `THREADS`         | 每进程线程数       | `8`             | 建议 2-16                          |
| `SESSION_TIMEOUT` | 会话超时时间(秒)    | `3600`          | 任何正整数                            |
| `TZ`              | 时区           | `Asia/Shanghai` | 标准时区名称                           |

### 数据库配置

#### SQLite（默认）

```bash
export DATABASE=sqlite3
```

数据文件位于 `./data/db.sqlite3`

#### MySQL

```bash
export DATABASE=mysql
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=rustdesk
export MYSQL_PASSWORD=yourpassword
export MYSQL_DATABASE=rustdesk_api
```

#### PostgreSQL

```bash
export DATABASE=postgresql
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=rustdesk
export POSTGRES_PASSWORD=yourpassword
export POSTGRES_DB=rustdesk_api
```

## 📡 API 文档

### 客户端 API

#### 认证相关

**登录**

```http
POST /api/client/login
Content-Type: application/json

{
    "username": "user",
    "password": "pass",
    "uuid": "device-uuid"
}
```

**登出**

```http
POST /api/client/logout
Authorization: Bearer <token>
```

**获取当前用户**

```http
GET /api/client/currentUser
Authorization: Bearer <token>
```

#### 设备管理

**心跳检测**

```http
POST /api/client/heartbeat
Authorization: Bearer <token>

{
    "uuid": "device-uuid",
    "peer_id": "peer-id",
    "ver": "1.2.3"
}
```

**系统信息上报**

```http
POST /api/client/sysinfo
Authorization: Bearer <token>

{
    "uuid": "device-uuid",
    "peer_id": "peer-id",
    "cpu": "Intel Core i7",
    "memory": "16GB",
    "os": "Windows 11",
    "device_name": "MyComputer",
    "username": "user",
    "version": "1.2.3"
}
```

**获取设备列表**

```http
GET /api/client/peers
Authorization: Bearer <token>
```

#### 地址簿管理

**获取地址簿列表**

```http
GET /api/client/ab
Authorization: Bearer <token>
```

**获取个人地址簿**

```http
GET /api/client/ab/personal
Authorization: Bearer <token>
```

**添加设备到地址簿**

```http
POST /api/client/ab/peer/add/{guid}
Authorization: Bearer <token>

{
    "peer_id": "peer-id",
    "alias": "device-alias"
}
```

**更新设备信息**

```http
PUT /api/client/ab/peer/update/{guid}
Authorization: Bearer <token>

{
    "peer_id": "peer-id",
    "alias": "new-alias"
}
```

**删除设备**

```http
DELETE /api/client/ab/peer/{guid}?peer_id={peer_id}
Authorization: Bearer <token>
```

**获取标签列表**

```http
GET /api/client/ab/tags/{guid}
Authorization: Bearer <token>
```

**添加/更新标签**

```http
POST /api/client/ab/tag/add/{guid}
Authorization: Bearer <token>

{
    "name": "tag-name",
    "color": "#FF0000"
}
```

**重命名标签**

```http
PUT /api/client/ab/tag/rename/{guid}
Authorization: Bearer <token>

{
    "old_name": "old-tag",
    "new_name": "new-tag"
}
```

#### 审计日志

**获取连接日志**

```http
GET /api/client/audit/conn
Authorization: Bearer <token>
```

**获取文件传输日志**

```http
GET /api/client/audit/file
Authorization: Bearer <token>
```

### Web 管理 API

#### 认证

```http
POST /web/login
GET  /web/logout
```

#### 设备管理

```http
GET  /web/home                    # 首页
POST /web/device/rename-alias     # 重命名设备
GET  /web/device/detail           # 设备详情
POST /web/device/update           # 更新设备
GET  /web/device/statuses         # 设备状态
```

#### 用户管理

```http
POST /web/user/create             # 创建用户
POST /web/user/update             # 更新用户
POST /web/user/reset-password     # 重置密码
POST /web/user/delete             # 删除用户
```

#### 地址簿管理

```http
GET  /web/personal/list           # 地址簿列表
POST /web/personal/create         # 创建地址簿
POST /web/personal/delete         # 删除地址簿
POST /web/personal/rename         # 重命名地址簿
GET  /web/personal/detail         # 地址簿详情
POST /web/personal/add-device     # 添加设备
POST /web/personal/remove-device  # 移除设备
POST /web/personal/update-alias   # 更新别名
POST /web/personal/update-tags    # 更新标签
```

## 💾 数据库模型

### 核心模型

| 模型              | 说明              |
|-----------------|-----------------|
| `User`          | 用户账户（Django 内置） |
| `Token`         | 用户认证令牌          |
| `HeartBeat`     | 客户端心跳记录         |
| `PeerInfo`      | 客户端系统信息         |
| `Personal`      | 地址簿             |
| `Tag`           | 设备标签            |
| `ClientTags`    | 设备标签关联          |
| `Alias`         | 设备别名            |
| `LoginClient`   | 登录客户端记录         |
| `Log`           | 操作日志            |
| `AutidConnLog`  | 连接审计日志          |
| `AuditFileLog`  | 文件传输审计日志        |
| `UserPrefile`   | 用户配置            |
| `UserPersonal`  | 用户地址簿关联         |
| `PeerPersonal`  | 设备地址簿关联         |
| `SharePersonal` | 地址簿分享记录         |
| `UserConfig`    | 用户配置项           |

### 数据库关系

```
User (用户)
  ├─→ Token (令牌)
  ├─→ Personal (地址簿)
  ├─→ ClientTags (设备标签)
  ├─→ LoginClient (登录客户端)
  └─→ UserConfig (用户配置)

PeerInfo (设备信息)
  ├─→ HeartBeat (心跳)
  ├─→ PeerPersonal (地址簿关联)
  ├─→ Alias (别名)
  ├─→ AutidConnLog (连接日志)
  └─→ AuditFileLog (文件日志)

Personal (地址簿)
  ├─→ UserPersonal (用户关联)
  ├─→ PeerPersonal (设备关联)
  └─→ SharePersonal (分享记录)
```

## 🔧 开发指南

### 本地开发

1. **启用调试模式**

```bash
export DEBUG=True
```

2. **运行开发服务器**

```bash
python manage.py runserver
```

3. **访问调试工具**

访问 `http://localhost:8000/__debug__/` 查看 Django Debug Toolbar

### 创建管理命令

在 `apps/commands/management/commands/` 目录下创建新命令：

```python
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = '命令描述'
    
    def handle(self, *args, **options):
        # 命令逻辑
        pass
```

运行命令：

```bash
python manage.py your_command
```

### 数据库迁移

```bash
# 创建迁移文件
python manage.py makemigrations

# 应用迁移
python manage.py migrate

# 查看迁移状态
python manage.py showmigrations
```

### 代码规范

- 使用 reStructuredText 格式编写函数注释
- 遵循 PEP 8 代码规范
- 确保跨平台兼容性（Windows、macOS、Linux）

## ❓ 常见问题

### 1. 数据库锁定错误

**问题**: SQLite 出现数据库锁定错误

**解决方案**:

- 使用 MySQL 或 PostgreSQL
- 减少并发写入操作
- 调整 `WORKERS` 和 `THREADS` 参数

### 2. 会话过期问题

**问题**: 用户频繁需要重新登录

**解决方案**:

```bash
# 增加会话超时时间（秒）
export SESSION_TIMEOUT=86400  # 24小时
```

### 3. 跨域问题

**问题**: Web 管理界面无法访问 API

**解决方案**:

- 确保使用相同的域名和端口
- 配置 CORS 中间件（如需要）

### 4. Docker 容器无法启动

**问题**: Docker 容器启动失败

**解决方案**:

```bash
# 查看日志
docker logs rustdesk_api

# 重新构建
docker-compose down
docker-compose up --build
```

### 5. 静态文件无法加载

**问题**: CSS/JS 文件 404

**解决方案**:

```bash
# 重新收集静态文件
python manage.py collectstatic --noinput
```

## 🤝 贡献指南

我们欢迎任何形式的贡献！

### 贡献流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发规范

- 编写清晰的提交信息
- 添加必要的测试
- 更新相关文档
- 确保代码通过 linting 检查

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [RustDesk](https://github.com/rustdesk/rustdesk) - 优秀的远程桌面软件
- [Django](https://www.djangoproject.com/) - 强大的 Web 框架
- 所有贡献者

## 📮 联系方式

- 作者: 御风
- Issues: [GitHub Issues](https://github.com/yourusername/rustdesk_api/issues)

---

<div align="center">

Made with ❤️ by 御风

[English](./README_EN.md) | 中文

</div>
