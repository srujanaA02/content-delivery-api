import os
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, File, UploadFile, HTTPException, Request, Response
from app.models.database import database, assets, asset_versions, access_tokens
from app.services.storage import upload_file, get_file, calculate_etag

router = APIRouter()


# ── POST /assets/upload ──────────────────────────────────────────
@router.post("/upload", status_code=201)
async def upload_asset(file: UploadFile = File(...)):
    file_bytes = await file.read()
    etag = calculate_etag(file_bytes)
    object_key = f"uploads/{uuid.uuid4()}/{file.filename}"

    upload_file(file_bytes, object_key, file.content_type)

    asset_id = str(uuid.uuid4())
    query = assets.insert().values(
        id=asset_id,
        object_storage_key=object_key,
        filename=file.filename,
        mime_type=file.content_type,
        size_bytes=len(file_bytes),
        etag=etag,
        is_private=False,
    )
    await database.execute(query)

    asset = await database.fetch_one(assets.select().where(assets.c.id == asset_id))
    return dict(asset)


# ── GET /assets/{id}/download ────────────────────────────────────
@router.get("/{asset_id}/download")
async def download_asset(asset_id: str, request: Request, response: Response):
    asset = await database.fetch_one(assets.select().where(assets.c.id == asset_id))
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    asset = dict(asset)
    etag_value = f'"{asset["etag"]}"'
    last_modified = asset["updated_at"].strftime("%a, %d %b %Y %H:%M:%S GMT")

    response.headers["ETag"] = etag_value
    response.headers["Last-Modified"] = last_modified
    response.headers["Cache-Control"] = "public, s-maxage=3600, max-age=60"

    # ✅ 304 Not Modified if ETag matches
    client_etag = request.headers.get("if-none-match")
    if client_etag and client_etag == etag_value:
        return Response(status_code=304, headers=dict(response.headers))

    file_bytes = get_file(asset["object_storage_key"])
    return Response(
        content=file_bytes,
        media_type=asset["mime_type"],
        headers={
            "ETag": etag_value,
            "Last-Modified": last_modified,
            "Cache-Control": "public, s-maxage=3600, max-age=60",
            "Content-Length": str(len(file_bytes)),
        },
    )


# ── HEAD /assets/{id}/download ───────────────────────────────────
@router.head("/{asset_id}/download")
async def head_asset(asset_id: str, response: Response):
    asset = await database.fetch_one(assets.select().where(assets.c.id == asset_id))
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    asset = dict(asset)
    response.headers["ETag"] = f'"{asset["etag"]}"'
    response.headers["Last-Modified"] = asset["updated_at"].strftime("%a, %d %b %Y %H:%M:%S GMT")
    response.headers["Cache-Control"] = "public, s-maxage=3600, max-age=60"
    response.headers["Content-Type"] = asset["mime_type"]
    response.headers["Content-Length"] = str(asset["size_bytes"])
    return Response(status_code=200, headers=dict(response.headers))


# ── POST /assets/{id}/publish ────────────────────────────────────
@router.post("/{asset_id}/publish")
async def publish_asset(asset_id: str):
    asset = await database.fetch_one(assets.select().where(assets.c.id == asset_id))
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    asset = dict(asset)
    version_id = str(uuid.uuid4())

    await database.execute(asset_versions.insert().values(
        id=version_id,
        asset_id=asset_id,
        object_storage_key=asset["object_storage_key"],
        etag=asset["etag"],
    ))

    await database.execute(
        assets.update()
        .where(assets.c.id == asset_id)
        .values(current_version_id=version_id, updated_at=datetime.now(timezone.utc))
    )

    return {"message": "Published successfully", "version_id": version_id}


# ── GET /assets/public/{version_id} ─────────────────────────────
@router.get("/public/{version_id}")
async def get_public_version(version_id: str):
    query = """
        SELECT av.*, a.mime_type, a.size_bytes
        FROM asset_versions av
        JOIN assets a ON av.asset_id = a.id
        WHERE av.id = :version_id
    """
    version = await database.fetch_one(query=query, values={"version_id": version_id})
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    version = dict(version)
    file_bytes = get_file(version["object_storage_key"])

    return Response(
        content=file_bytes,
        media_type=version["mime_type"],
        headers={
            "ETag": f'"{version["etag"]}"',
            "Last-Modified": version["created_at"].strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "Cache-Control": "public, max-age=31536000, immutable",
            "Content-Length": str(len(file_bytes)),
        },
    )


# ── POST /assets/{id}/token ──────────────────────────────────────
@router.post("/{asset_id}/token", status_code=201)
async def generate_token(asset_id: str):
    asset = await database.fetch_one(assets.select().where(assets.c.id == asset_id))
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    token = secrets.token_hex(32)
    expiry_hours = int(os.getenv("TOKEN_EXPIRY_HOURS", 1))
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)

    await database.execute(access_tokens.insert().values(
        token=token,
        asset_id=asset_id,
        expires_at=expires_at,
    ))

    return {"token": token, "expires_at": expires_at}


# ── GET /assets/private/{token} ──────────────────────────────────
@router.get("/private/{token}")
async def get_private_asset(token: str):
    query = """
        SELECT at.*, a.object_storage_key, a.mime_type, a.size_bytes,
               a.etag, a.updated_at
        FROM access_tokens at
        JOIN assets a ON at.asset_id = a.id
        WHERE at.token = :token
    """
    result = await database.fetch_one(query=query, values={"token": token})

    if not result:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = dict(result)
    if datetime.now(timezone.utc) > result["expires_at"]:
        raise HTTPException(status_code=401, detail="Token expired")

    file_bytes = get_file(result["object_storage_key"])

    return Response(
        content=file_bytes,
        media_type=result["mime_type"],
        headers={
            "ETag": f'"{result["etag"]}"',
            "Last-Modified": result["updated_at"].strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "Cache-Control": "private, no-store, no-cache, must-revalidate",
            "Content-Length": str(len(file_bytes)),
        },
    )