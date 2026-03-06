# 🚀 Content Delivery API

A high-performance content delivery API with HTTP edge caching, built with **FastAPI**, **PostgreSQL**, and **MinIO**.

---

## ✅ Features

- File upload with SHA-256 ETag generation
- Conditional GET requests (`304 Not Modified`)
- Cache-Control headers for public, versioned, and private content
- Immutable versioned asset URLs
- Secure short-lived private access tokens
- MinIO object storage (S3-compatible)
- Full Docker setup — one command to run everything

---

## 🛠️ Prerequisites — Install These First

Download and install all of these before starting:

| Tool | Download Link | Notes |
|------|--------------|-------|
| **Git** | https://git-scm.com/download/win | Keep all defaults during install |
| **Python 3.11+** | https://www.python.org/downloads/ | ⚠️ Tick "Add to PATH" during install! |
| **Docker Desktop** | https://www.docker.com/products/docker-desktop/ | Restart PC after install |
| **VS Code** | https://code.visualstudio.com/download | Optional but recommended |

After installing, open a terminal and verify:

```bash
python --version
git --version
docker --version
```

All should show version numbers. ✅

---

## 📥 Step 1 — Clone the Repository

```bash
# Go to Desktop (or any folder you prefer)
cd Desktop

# Clone the repo
git clone https://github.com/srujanaA02/content-delivery-api.git

# Enter the project folder
cd content-delivery-api
```

---

## ⚙️ Step 2 — Set Up Environment Variables

```bash
# Copy the example env file
cp .env.example .env
```

The `.env` file is already pre-filled for local development. No changes needed.

If you want to check it:
```bash
cat .env
```

It should look like:
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/contentdb
MINIO_ENDPOINT=localhost
MINIO_PORT=9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=assets
TOKEN_EXPIRY_HOURS=1
```

---

## 🐳 Step 3 — Start Everything with Docker

> ⚠️ Make sure **Docker Desktop is open and running** before this step!

```bash
# Build and start all services (API + PostgreSQL + MinIO)
docker-compose up --build
```

Wait ~2 minutes. You should see:

```
✅ Tables created
✅ Database connected
✅ MinIO bucket created
INFO:     Uvicorn running on http://0.0.0.0:3000
```

### Services running:

| Service | URL | Credentials |
|---------|-----|-------------|
| **API** | http://localhost:3000 | — |
| **API Docs (Swagger)** | http://localhost:3000/docs | — |
| **MinIO Dashboard** | http://localhost:9001 | minioadmin / minioadmin |

---

## 🧪 Step 4 — Test the API

Open a **new terminal** (keep Docker running in the first one), then run these commands one by one:

### Health Check
```bash
curl http://localhost:3000/health
```
Expected: `{"status":"OK"}` ✅

---

### Upload a File
```bash
# First create a test file
echo "Hello World Test File" > testfile.txt

# Upload it
curl -X POST http://localhost:3000/assets/upload \
  -F "file=@testfile.txt"
```

Expected response:
```json
{
  "id": "f06e304b-xxxx-xxxx-xxxx-xxxxxxxx",
  "filename": "testfile.txt",
  "mime_type": "text/plain",
  "size_bytes": 22,
  "etag": "b8deafe9dc46f7f0...",
  "is_private": false,
  "created_at": "2026-03-06T07:01:26Z"
}
```

> 📋 **Copy the `id` and `etag` values** — you'll need them for the next steps!

---

### Download a File
```bash
curl http://localhost:3000/assets/YOUR-ID-HERE/download -v
```

Look for these headers in the response:
```
ETag: "b8deafe9..."
Cache-Control: public, s-maxage=3600, max-age=60
Last-Modified: Fri, 06 Mar 2026 07:01:26 GMT
```

---

### Test 304 Not Modified (Caching!)
```bash
curl -H 'If-None-Match: "YOUR-ETAG-HERE"' \
  http://localhost:3000/assets/YOUR-ID-HERE/download -v
```

Expected: `HTTP/1.1 304 Not Modified` with empty body ✅

---

### HEAD Request (Headers Only)
```bash
curl -I http://localhost:3000/assets/YOUR-ID-HERE/download
```

Returns all headers but no file body. ✅

---

### Publish an Immutable Version
```bash
curl -X POST http://localhost:3000/assets/YOUR-ID-HERE/publish
```

Expected:
```json
{
  "message": "Published successfully",
  "version_id": "10fb2b00-xxxx-xxxx-xxxx-xxxxxxxx"
}
```

> 📋 **Copy the `version_id`** for the next step!

---

### Access Public Versioned URL (Immutable Cache)
```bash
curl http://localhost:3000/assets/public/YOUR-VERSION-ID-HERE -v
```

Look for:
```
Cache-Control: public, max-age=31536000, immutable
```
✅ This URL is cached by CDN for 1 full year!

---

### Generate a Private Access Token
```bash
curl -X POST http://localhost:3000/assets/YOUR-ID-HERE/token
```

Expected:
```json
{
  "token": "33bc467099ddc0e6...",
  "expires_at": "2026-03-06T08:03:01Z"
}
```

> 📋 **Copy the `token`** for the next step!

---

### Access Private File with Token
```bash
curl http://localhost:3000/assets/private/YOUR-TOKEN-HERE -v
```

Look for:
```
Cache-Control: private, no-store, no-cache, must-revalidate
```
✅

---

### Test Invalid Token (Should Return 401)
```bash
curl http://localhost:3000/assets/private/invalidtoken123 -v
```

Expected: `HTTP/1.1 401 Unauthorized` ✅

---

## 📊 Step 5 — Run the Benchmark

Open a **new terminal** (separate from Docker terminal):

```bash
# Install httpx if not already installed
pip install httpx --break-system-packages

# Run benchmark
python scripts/run_benchmark.py
```

Expected output:
```
🚀 Content Delivery API - Benchmark

📤 Uploading test file...
✅ Uploaded: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

📥 Testing 50 normal downloads...
   Avg: 1715.37ms
   Min: 1296.02ms
   Max: 2132.47ms

⚡ Testing 50 conditional requests (304)...
   Avg: 1871.94ms
   304 Hit Rate: 50/50 (100%)

📌 Publishing version...
🔒 Testing immutable versioned URL...
   Cache-Control: public, max-age=31536000, immutable
   ✅ Immutable: True

========================================
📊 BENCHMARK SUMMARY
========================================
Normal Download Avg  : 1715.37ms
Conditional Req Avg  : 1871.94ms
304 Cache Hit Rate   : 100%
Immutable Caching    : ✅ YES
========================================
```

---

## 🧬 Step 6 — Run Tests

```bash
# Run tests inside Docker
docker-compose run --rm app pytest tests/ -v
```

---

## 📁 Project Structure

```
content-delivery-api/
├── app/
│   ├── main.py                  # FastAPI app entry point
│   ├── routes/
│   │   └── assets.py            # All API endpoints
│   ├── services/
│   │   └── storage.py           # MinIO storage + ETag logic
│   └── models/
│       ├── database.py          # PostgreSQL tables + connection
│       └── schemas.py           # Pydantic response models
├── docs/
│   ├── README.md                # This file
│   ├── ARCHITECTURE.md          # System design
│   ├── API_DOCS.md              # Endpoint documentation
│   └── PERFORMANCE.md           # Benchmark results
├── scripts/
│   └── run_benchmark.py         # Performance benchmark script
├── tests/
│   └── test_assets.py           # API tests
├── docker-compose.yml           # Docker services config
├── Dockerfile                   # App container definition
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (local)
├── .env.example                 # Environment variables template
└── submission.yml               # Automated evaluation commands
```

---

## 🔌 API Endpoints Summary

| Method | Endpoint | Description | Cache-Control |
|--------|----------|-------------|---------------|
| `POST` | `/assets/upload` | Upload a file | — |
| `GET` | `/assets/:id/download` | Download with ETag caching | `public, s-maxage=3600, max-age=60` |
| `HEAD` | `/assets/:id/download` | Headers only, no body | `public, s-maxage=3600, max-age=60` |
| `POST` | `/assets/:id/publish` | Create immutable version | — |
| `GET` | `/assets/public/:version_id` | Serve immutable version | `public, max-age=31536000, immutable` |
| `POST` | `/assets/:id/token` | Generate private token | — |
| `GET` | `/assets/private/:token` | Access private file | `private, no-store, no-cache` |

---

## 🗄️ Database Schema

```sql
-- Stores file metadata
assets (id, object_storage_key, filename, mime_type, size_bytes, etag, current_version_id, is_private, created_at, updated_at)

-- Stores immutable versions
asset_versions (id, asset_id, object_storage_key, etag, created_at)

-- Stores short-lived private tokens
access_tokens (token, asset_id, expires_at, created_at)
```

---

## 🛑 Stop the Server

```bash
# Stop all Docker containers
docker-compose down

# Stop and delete all data (fresh start)
docker-compose down -v
```

---

## 🔧 Troubleshooting

| Problem | Fix |
|---------|-----|
| `docker: command not found` | Open Docker Desktop app first |
| `port 3000 already in use` | Run `docker-compose down` then retry |
| `ModuleNotFoundError` | Run `docker-compose up --build` (rebuilds with new packages) |
| `curl: connection refused` | Wait 30 more seconds for Docker to fully start |
| Files not showing in MinIO | Go to http://localhost:9001 and check the `assets` bucket |

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| Framework | FastAPI |
| Server | Uvicorn |
| Database | PostgreSQL 15 |
| Object Storage | MinIO (S3-compatible) |
| Containerization | Docker + Docker Compose |
| Caching | HTTP ETags + Cache-Control |
| Token Security | `secrets.token_hex(32)` |
