# RustDesk API 服务

这是一个基于 Django 框架开发的后端服务，主要用于支持 RustDesk 客户端的 API 请求。该项目实现了客户端认证、心跳检测、系统信息收集、用户管理、设备分组、日志记录等功能。

## 主要功能

- **客户端认证**：支持用户登录和登出操作，并通过 Token 验证身份。
- **心跳检测**：客户端定期发送心跳信息以保持在线状态。
- **系统信息**：收集并存储客户端的系统信息。
- **用户管理**：支持用户注册、查询、密码修改等操作。
- **设备分组**：支持为设备添加标签，便于分类管理。
- **日志记录**：记录客户端连接和文件传输的日志信息。

## 服务模块

- `apps/client_apis/views.py`：提供所有 API 接口的实现，包括登录、心跳、系统信息上报等。
- `apps/db/models.py`：定义数据库模型，包括心跳信息、系统信息、用户标签、登录记录等。
- `apps/db/service.py`：封装数据库操作，提供统一的数据访问接口，如用户服务、系统信息服务、标签服务等。

## 快速开始

### 环境要求

- Python 3.13
- Django 框架
- 数据库支持（如 PostgreSQL、MySQL）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务

```bash
./start.sh
```

服务默认运行在 `21114` 端口。

## 接口文档

### 登录接口

```http
POST /api/client/login
```

### 心跳接口

```http
POST /api/client/heartbeat
```

### 系统信息上报

```http
POST /api/client/sysinfo
```

### 获取用户设备列表

```http
GET /api/client/peers
```

### 获取当前用户信息

```http
GET /api/client/current_user
```

## 数据库模型

- `HeartBeat`：记录客户端的心跳信息。
- `SystemInfo`：存储客户端的系统信息。
- `Tag`：设备标签，用于设备分组。
- `Token`：用户 Token，用于身份验证。
- `Log`：记录客户端操作日志。
- `AutidConnLog`：记录客户端连接日志。
- `AuditFileLog`：记录文件传输日志。

## 服务接口

- `UserService`：用户管理服务，提供用户注册、查询、密码修改等功能。
- `SystemInfoService`：系统信息服务，提供客户端信息查询和更新功能。
- `HeartBeatService`：心跳服务，用于检测客户端是否在线。
- `TokenService`：Token 管理服务，用于生成和验证用户 Token。
- `TagService`：标签服务，用于管理设备标签。

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。