# API Documentation

## POST /assets/upload
Upload a file to object storage.

**Request:** `multipart/form-data` with `file` field

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "filename": "test.txt",
  "mime_type": "text/plain",
  "size_bytes": 22,
  "etag": "sha256hash",
  "is_private": false,
  "created_at": "2026-03-06T07:01:26Z"
}
```

---

## GET /assets/:id/download
Download a file. Supports conditional requests.

**Headers (optional):** `If-None-Match: "etag"`

**Response:**
- `200 OK` — file content with caching headers
- `304 Not Modified` — if ETag matches (empty body, saves bandwidth!)

**Response Headers:**
```
ETag: "sha256hash"
Cache-Control: public, s-maxage=3600, max-age=60
Last-Modified: Fri, 06 Mar 2026 07:01:26 GMT
```

---

## HEAD /assets/:id/download
Check file metadata without downloading body.

**Response:** `200 OK` with all headers, no body

---

## POST /assets/:id/publish
Create an immutable version of an asset.

**Response:** `200 OK`
```json
{
  "message": "Published successfully",
  "version_id": "uuid"
}
```

---

## GET /assets/public/:version_id
Serve an immutable versioned asset. Designed for CDN caching.

**Response Headers:**
```
Cache-Control: public, max-age=31536000, immutable
```

---

## POST /assets/:id/token
Generate a short-lived private access token.

**Response:** `201 Created`
```json
{
  "token": "hex_token",
  "expires_at": "2026-03-06T08:03:01Z"
}
```

---

## GET /assets/private/:token
Access a private file using a valid token.

**Response:**
- `200 OK` — file with private cache headers
- `401 Unauthorized` — invalid or expired token

**Response Headers:**
```
Cache-Control: private, no-store, no-cache, must-revalidate
```