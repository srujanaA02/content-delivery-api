import pytest
import httpx

BASE_URL = "http://app:3000"


def test_health():
    r = httpx.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    assert r.json() == {"status": "OK"}


def test_upload():
    files = {"file": ("test.txt", b"Hello World Test", "text/plain")}
    r = httpx.post(f"{BASE_URL}/assets/upload", files=files)
    assert r.status_code == 201
    data = r.json()
    assert "id" in data
    assert "etag" in data
    assert data["filename"] == "test.txt"


def test_download_and_304():
    # Upload first
    files = {"file": ("cache_test.txt", b"Cache Test Content", "text/plain")}
    upload = httpx.post(f"{BASE_URL}/assets/upload", files=files)
    assert upload.status_code == 201
    asset_id = upload.json()["id"]
    etag = upload.json()["etag"]

    # Normal download - should return 200
    r = httpx.get(f"{BASE_URL}/assets/{asset_id}/download")
    assert r.status_code == 200
    assert "etag" in r.headers
    assert "cache-control" in r.headers

    # Conditional request - should return 304
    r304 = httpx.get(
        f"{BASE_URL}/assets/{asset_id}/download",
        headers={"If-None-Match": f'"{etag}"'}
    )
    assert r304.status_code == 304


def test_head_request():
    files = {"file": ("head_test.txt", b"Head Test", "text/plain")}
    upload = httpx.post(f"{BASE_URL}/assets/upload", files=files)
    asset_id = upload.json()["id"]

    r = httpx.head(f"{BASE_URL}/assets/{asset_id}/download")
    assert r.status_code == 200
    assert "etag" in r.headers
    assert "cache-control" in r.headers


def test_publish_version():
    files = {"file": ("version_test.txt", b"Version Test", "text/plain")}
    upload = httpx.post(f"{BASE_URL}/assets/upload", files=files)
    asset_id = upload.json()["id"]

    r = httpx.post(f"{BASE_URL}/assets/{asset_id}/publish")
    assert r.status_code == 200
    assert "version_id" in r.json()


def test_public_versioned_url():
    # Upload and publish
    files = {"file": ("immutable_test.txt", b"Immutable Content", "text/plain")}
    upload = httpx.post(f"{BASE_URL}/assets/upload", files=files)
    asset_id = upload.json()["id"]

    pub = httpx.post(f"{BASE_URL}/assets/{asset_id}/publish")
    version_id = pub.json()["version_id"]

    # Access public versioned URL
    r = httpx.get(f"{BASE_URL}/assets/public/{version_id}")
    assert r.status_code == 200
    assert "immutable" in r.headers.get("cache-control", "")


def test_private_token():
    files = {"file": ("private_test.txt", b"Private Content", "text/plain")}
    upload = httpx.post(f"{BASE_URL}/assets/upload", files=files)
    asset_id = upload.json()["id"]

    # Generate token
    token_resp = httpx.post(f"{BASE_URL}/assets/{asset_id}/token")
    assert token_resp.status_code == 201
    token = token_resp.json()["token"]

    # Access with valid token
    r = httpx.get(f"{BASE_URL}/assets/private/{token}")
    assert r.status_code == 200
    assert "no-store" in r.headers.get("cache-control", "")


def test_invalid_token():
    r = httpx.get(f"{BASE_URL}/assets/private/totallyinvalidtoken999")
    assert r.status_code == 401