# VideoFlix Backend API

VideoFlix is a robust backend API for a video streaming platform, built with Django and Django REST Framework (DRF). It supports user authentication, video management, HLS (HTTP Live Streaming) delivery, asynchronous task processing with RQ, and is fully Dockerized for easy deployment.

## ✨ Features
- **User Authentication**: JWT-based auth with cookie support, registration, activation, login/logout, password reset.
- **Video Management**: Upload, list videos with HLS streaming support (manifest and segments).
- **Streaming**: Adaptive bitrate HLS streaming with segment delivery.
- **Async Tasks**: RQ + Redis for background jobs.
- **Media Handling**: Static/media/video file serving, Pillow for image processing.
- **CORS Enabled**: Ready for integration with frontend apps (e.g., on port 5500).
- **Admin Interface**: Django admin for management.
- **Monitoring**: Django RQ dashboard.

## 🛠️ Tech Stack
### Backend
- **Django 6.0.2** - Web framework
- **Django REST Framework 3.16.1** - API framework
- **djangorestframework-simplejwt 5.5.1** - JWT authentication (access/refresh tokens with cookies)
- **PostgreSQL** - Primary database (via psycopg2-binary)
- **Redis** - Caching and task queue (django-redis, RQ 2.6.1, django-rq)
- **Pillow 12.1.1** - Image/video thumbnail processing
- **django-cors-headers 4.9.0** - Cross-origin requests
- **Whitenoise 6.11.0** - Static files serving
- **Gunicorn 25.0.2** - WSGI server

### Infrastructure
- **Docker & Docker Compose** - Containerization (postgres, redis, web services)
- **RQ** - Distributed task queue
- **SMTP** - Email backend (configurable, defaults to MailHog/console)
- **FFmpeg** - Video processing/transcoding for HLS

### Development
- **django-debug-toolbar** - Debug tools
- **python-dotenv** - Environment variables

Full dependencies: See [requirements.txt](requirements.txt).

## 📋 Prerequisites & Installation

### Install Docker & Docker Compose (Linux/Ubuntu)
1. Update packages: `sudo apt update`
2. Install prerequisites: `sudo apt install ca-certificates curl`
3. Add Docker GPG key: `sudo install -m 0755 -d /etc/apt/keyrings && sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc && sudo chmod a+r /etc/apt/keyrings/docker.asc`
4. Add repo: `echo \"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable\" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null`
5. Install: `sudo apt update && sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin`
6. Start & enable: `sudo systemctl start docker && sudo systemctl enable docker`
7. Add user to group: `sudo usermod -aG docker $USER` (relogin)

Official guide: [Docker Docs](https://docs.docker.com/engine/install/ubuntu/)

### Install FFmpeg (Linux/Ubuntu)
```bash
sudo apt update
sudo apt install ffmpeg
```
- Required for video transcoding to HLS segments (e.g., `ffmpeg -i input.mp4 -hls_time 10 ...`).
- In Docker: Ensure FFmpeg installed in `backend.Dockerfile` (add `RUN apt-get update && apt-get install -y ffmpeg` if missing).

### Other Prerequisites
- Python 3.12+ (for local dev)
- PostgreSQL & Redis (handled by Docker)

Copy `.env.example` to `.env` and update secrets (if no `.env.example`, create from sample below):
```
SECRET_KEY=your_django_secret_key_here
DB_NAME=videoflix_db
DB_USER=videoflix_user
DB_PASSWORD=supersecretpassword
DB_HOST=db
DB_PORT=5432
REDIS_HOST=redis
REDIS_PORT=6379
EMAIL_HOST=mailhog
EMAIL_PORT=1025
EMAIL_USE_TLS=False
EMAIL_HOST_USER=admin@gmail.com
EMAIL_HOST_PASSWORD=securepassword
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

## 🚀 Quick Start

### With Docker (Recommended)
```bash
docker-compose up --build
```
- Backend: `http://localhost:8000`
- Admin: `http://localhost:8000/admin/`
- RQ Dashboard: `http://localhost:8000/django-rq/`
- Superuser: `docker-compose exec web python manage.py createsuperuser`

### Local Development
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Migrate/Collect static:
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
```

## 🔌 API Endpoints

All under `/api/`. Use JWT cookies/headers for auth.

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register/` | Register user |
| GET | `/api/activate/<uidb64>/<token>/` | Activate account |
| POST | `/api/login/` | Login (JWT cookies) |
| POST | `/api/logout/` | Logout |
| POST | `/api/token/refresh/` | Refresh token |
| POST | `/api/password_reset/` | Reset password email |
| POST | `/api/password_confirm/<uidb64>/<token>/` | Confirm reset |

### Videos
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/video/` | List videos | Optional |
| GET | `/api/video/<id>/<resolution>/index.m3u8` | HLS manifest | Optional |
| GET | `/api/video/<id>/<resolution>/<segment>` | HLS segment | Optional |

### Other
| Endpoint | Description |
|----------|-------------|
| `/admin/` | Admin panel |
| `/django-rq/` | RQ dashboard |

## 📁 Structure
```
videoflix/
├── auth_app/     # Auth
├── videoflix_app/ # Videos/HLS
├── core/         # Settings
├── docker-compose.yml
├── requirements.txt
└── manage.py
```


