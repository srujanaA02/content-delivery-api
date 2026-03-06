from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AssetResponse(BaseModel):
    id: str
    filename: str
    mime_type: str
    size_bytes: int
    etag: str
    current_version_id: Optional[str]
    is_private: bool
    created_at: datetime
    updated_at: datetime

class VersionResponse(BaseModel):
    id: str
    asset_id: str
    object_storage_key: str
    etag: str
    created_at: datetime

class TokenResponse(BaseModel):
    token: str
    expires_at: datetime