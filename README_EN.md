<div align="center">

# RustDesk API Server

English | [中文](./README.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Django Version](https://img.shields.io/badge/django-5.2-green.svg)](https://www.djangoproject.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

A fully-featured RustDesk API server providing client authentication, device management, address book management, audit
logging and more.

</div>

---

## 📖 Table of Contents

- [Features](#features)
- [System Architecture](#system-architecture)
- [Quick Start](#quick-start)
    - [Requirements](#requirements)
    - [Docker Deployment (Recommended)](#docker-deployment-recommended)
    - [Manual Deployment](#manual-deployment)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
    - [Client API](#client-api)
    - [Web Management API](#web-management-api)
- [Database Models](#database-models)
- [Development Guide](#development-guide)
- [FAQ](#faq)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### Core Features

- 🔐 **User Authentication System** - Support user registration, login, token management
- 💓 **Heartbeat Detection** - Real-time monitoring of client online status
- 📊 **System Information Collection** - Automatically collect and store client system information
- 🏷️ **Device Tag Management** - Support device grouping and tag management
- 📒 **Address Book Management** - Support personal and shared address books
- 📝 **Audit Logging** - Record connection and file transfer logs
- 🌐 **Multi-language Support** - Support Chinese and English interfaces
- 🎨 **Web Admin Interface** - Provide friendly web admin backend

### Technical Features

- 🚀 **High Performance** - Based on Django + Gunicorn, supports multi-process and multi-threading
- 🐳 **Containerized Deployment** - Complete Docker support
- 💾 **Multi-database Support** - Support SQLite, MySQL, PostgreSQL
- 🔧 **Flexible Configuration** - Easy configuration through environment variables
- 📱 **Cross-platform** - Support Windows, macOS, Linux

## 🏗️ System Architecture

```
rustdesk_api/
├── apps/
│   ├── client_apis/      # Client API interfaces
│   │   ├── views.py      # Core API views
│   │   ├── view_ab.py    # Address book API
│   │   └── view_audit.py # Audit log API
│   ├── web/              # Web admin interface
│   │   ├── view_auth.py  # Authentication views
│   │   ├── view_home.py  # Home views
│   │   ├── view_user.py  # User management
│   │   └── view_personal.py # Address book management
│   ├── db/               # Database models and services
│   │   ├── models.py     # Data model definitions
│   │   └── service.py    # Database service layer
│   ├── commands/         # Management commands
│   └── common/           # Common middleware
├── common/               # Common utilities
│   ├── db_config.py      # Database configuration
│   ├── env.py            # Environment variable management
│   ├── logging_config.py # Logging configuration
│   └── utils.py          # Utility functions
├── static/               # Static files
├── templates/            # Template files
└── rustdesk_api/         # Django project configuration
```

## 🚀 Quick Start

### Requirements

- Python 3.13+
- Docker & Docker Compose (for containerized deployment)
- SQLite / MySQL / PostgreSQL (database)

### Docker Deployment (Recommended)

1. **Clone the project**

```bash
git clone https://github.com/yourusername/rustdesk_api.git
cd rustdesk_api
```

2. **Start the service**

```bash
docker-compose up -d
```

3. **Access the service**

- API Service: `http://localhost:21114`
- Web Admin: `http://localhost:21114/web/`

The service will automatically complete database migration and initialization.

### Manual Deployment

1. **Clone the project**

```bash
git clone https://github.com/yourusername/rustdesk_api.git
cd rustdesk_api
```

2. **Create virtual environment**

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

```bash
# Create .env file or set environment variables
export DATABASE=sqlite3
export DEBUG=False
export WORKERS=4
export THREADS=8
```

5. **Database migration**

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

6. **Create admin account**

```bash
python manage.py createsuperuser
```

7. **Start the service**

```bash
# Development
python manage.py runserver 0.0.0.0:21114

# Production
./start.sh
```

## ⚙️ Configuration

### Environment Variables

| Variable          | Description               | Default         | Options                          |
|-------------------|---------------------------|-----------------|----------------------------------|
| `DATABASE`        | Database type             | `sqlite3`       | `sqlite3`, `mysql`, `postgresql` |
| `DEBUG`           | Debug mode                | `False`         | `True`, `False`                  |
| `HOST`            | Listen address            | `0.0.0.0`       | Any valid IP                     |
| `PORT`            | Listen port               | `21114`         | 1-65535                          |
| `WORKERS`         | Gunicorn worker count     | `4`             | Recommended 2-8                  |
| `THREADS`         | Threads per worker        | `8`             | Recommended 2-16                 |
| `SESSION_TIMEOUT` | Session timeout (seconds) | `3600`          | Any positive integer             |
| `TZ`              | Timezone                  | `Asia/Shanghai` | Standard timezone name           |

### Database Configuration

#### SQLite (Default)

```bash
export DATABASE=sqlite3
```

Data file located at `./data/db.sqlite3`

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

## 📡 API Documentation

### Client API

#### Authentication

**Login**

```http
POST /api/client/login
Content-Type: application/json

{
    "username": "user",
    "password": "pass",
    "uuid": "device-uuid"
}
```

**Logout**

```http
POST /api/client/logout
Authorization: Bearer <token>
```

**Get Current User**

```http
GET /api/client/currentUser
Authorization: Bearer <token>
```

#### Device Management

**Heartbeat**

```http
POST /api/client/heartbeat
Authorization: Bearer <token>

{
    "uuid": "device-uuid",
    "peer_id": "peer-id",
    "ver": "1.2.3"
}
```

**System Information Report**

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

**Get Device List**

```http
GET /api/client/peers
Authorization: Bearer <token>
```

#### Address Book Management

**Get Address Book List**

```http
GET /api/client/ab
Authorization: Bearer <token>
```

**Get Personal Address Book**

```http
GET /api/client/ab/personal
Authorization: Bearer <token>
```

**Add Device to Address Book**

```http
POST /api/client/ab/peer/add/{guid}
Authorization: Bearer <token>

{
    "peer_id": "peer-id",
    "alias": "device-alias"
}
```

**Update Device Information**

```http
PUT /api/client/ab/peer/update/{guid}
Authorization: Bearer <token>

{
    "peer_id": "peer-id",
    "alias": "new-alias"
}
```

**Delete Device**

```http
DELETE /api/client/ab/peer/{guid}?peer_id={peer_id}
Authorization: Bearer <token>
```

**Get Tag List**

```http
GET /api/client/ab/tags/{guid}
Authorization: Bearer <token>
```

**Add/Update Tag**

```http
POST /api/client/ab/tag/add/{guid}
Authorization: Bearer <token>

{
    "name": "tag-name",
    "color": "#FF0000"
}
```

**Rename Tag**

```http
PUT /api/client/ab/tag/rename/{guid}
Authorization: Bearer <token>

{
    "old_name": "old-tag",
    "new_name": "new-tag"
}
```

#### Audit Logs

**Get Connection Logs**

```http
GET /api/client/audit/conn
Authorization: Bearer <token>
```

**Get File Transfer Logs**

```http
GET /api/client/audit/file
Authorization: Bearer <token>
```

### Web Management API

#### Authentication

```http
POST /web/login
GET  /web/logout
```

#### Device Management

```http
GET  /web/home                    # Home page
POST /web/device/rename-alias     # Rename device
GET  /web/device/detail           # Device details
POST /web/device/update           # Update device
GET  /web/device/statuses         # Device statuses
```

#### User Management

```http
POST /web/user/create             # Create user
POST /web/user/update             # Update user
POST /web/user/reset-password     # Reset password
POST /web/user/delete             # Delete user
```

#### Address Book Management

```http
GET  /web/personal/list           # Address book list
POST /web/personal/create         # Create address book
POST /web/personal/delete         # Delete address book
POST /web/personal/rename         # Rename address book
GET  /web/personal/detail         # Address book details
POST /web/personal/add-device     # Add device
POST /web/personal/remove-device  # Remove device
POST /web/personal/update-alias   # Update alias
POST /web/personal/update-tags    # Update tags
```

## 💾 Database Models

### Core Models

| Model           | Description                      |
|-----------------|----------------------------------|
| `User`          | User account (Django built-in)   |
| `Token`         | User authentication token        |
| `HeartBeat`     | Client heartbeat records         |
| `PeerInfo`      | Client system information        |
| `Personal`      | Address book                     |
| `Tag`           | Device tags                      |
| `ClientTags`    | Device tag associations          |
| `Alias`         | Device aliases                   |
| `LoginClient`   | Login client records             |
| `Log`           | Operation logs                   |
| `AutidConnLog`  | Connection audit logs            |
| `AuditFileLog`  | File transfer audit logs         |
| `UserPrefile`   | User profile                     |
| `UserPersonal`  | User address book associations   |
| `PeerPersonal`  | Device address book associations |
| `SharePersonal` | Address book sharing records     |
| `UserConfig`    | User configuration items         |

### Database Relationships

```
User
  ├─→ Token
  ├─→ Personal
  ├─→ ClientTags
  ├─→ LoginClient
  └─→ UserConfig

PeerInfo
  ├─→ HeartBeat
  ├─→ PeerPersonal
  ├─→ Alias
  ├─→ AutidConnLog
  └─→ AuditFileLog

Personal
  ├─→ UserPersonal
  ├─→ PeerPersonal
  └─→ SharePersonal
```

## 🔧 Development Guide

### Local Development

1. **Enable debug mode**

```bash
export DEBUG=True
```

2. **Run development server**

```bash
python manage.py runserver
```

3. **Access debug tools**

Visit `http://localhost:8000/__debug__/` to view Django Debug Toolbar

### Creating Management Commands

Create new commands in `apps/commands/management/commands/`:

```python
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Command description'
    
    def handle(self, *args, **options):
        # Command logic
        pass
```

Run command:

```bash
python manage.py your_command
```

### Database Migrations

```bash
# Create migration files
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# View migration status
python manage.py showmigrations
```

### Code Standards

- Use reStructuredText format for function comments
- Follow PEP 8 code standards
- Ensure cross-platform compatibility (Windows, macOS, Linux)

## ❓ FAQ

### 1. Database Lock Error

**Problem**: SQLite database lock error

**Solution**:

- Use MySQL or PostgreSQL
- Reduce concurrent write operations
- Adjust `WORKERS` and `THREADS` parameters

### 2. Session Expiration

**Problem**: Users need to log in frequently

**Solution**:

```bash
# Increase session timeout (seconds)
export SESSION_TIMEOUT=86400  # 24 hours
```

### 3. CORS Issues

**Problem**: Web admin interface cannot access API

**Solution**:

- Ensure using the same domain and port
- Configure CORS middleware (if needed)

### 4. Docker Container Won't Start

**Problem**: Docker container fails to start

**Solution**:

```bash
# View logs
docker logs rustdesk_api

# Rebuild
docker-compose down
docker-compose up --build
```

### 5. Static Files Not Loading

**Problem**: CSS/JS files return 404

**Solution**:

```bash
# Recollect static files
python manage.py collectstatic --noinput
```

## 🤝 Contributing

We welcome all forms of contributions!

### Contribution Process

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Standards

- Write clear commit messages
- Add necessary tests
- Update relevant documentation
- Ensure code passes linting checks

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [RustDesk](https://github.com/rustdesk/rustdesk) - Excellent remote desktop software
- [Django](https://www.djangoproject.com/) - Powerful web framework
- All contributors

## 📮 Contact

- Author: 御风
- Issues: [GitHub Issues](https://github.com/JokerYF/rustdesk_api/issues)

---

<div align="center">

Made with ❤️ by 御风

English | [中文](./README.md)

</div>

