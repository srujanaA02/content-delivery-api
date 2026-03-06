import pytest
import httpx
import asyncio
from app.main import app

@pytest.mark.asyncio
async def test_health():
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}

@pytest.mark.asyncio
async def test_upload_and_download():
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        # Upload
        files = {"file": ("test.txt", b"Hello World", "text/plain")}
        upload_resp = await client.post("/assets/upload", files=files)
        assert upload_resp.status_code == 201
        asset = upload_resp.json()
        assert "etag" in asset
        assert "id" in asset

        asset_id = asset["id"]
        etag = asset["etag"]

        # Download
        download_resp = await client.get(f"/assets/{asset_id}/download")
        assert download_resp.status_code == 200
        assert download_resp.headers["etag"] == f'"{etag}"'
        assert "cache-control" in download_resp.headers

        # 304 Not Modified
        resp_304 = await client.get(
            f"/assets/{asset_id}/download",
            headers={"if-none-match": f'"{etag}"'}
        )
        assert resp_304.status_code == 304

@pytest.mark.asyncio
async def test_private_token_expired():
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/assets/private/invalidtoken123")
    assert resp.status_code == 401