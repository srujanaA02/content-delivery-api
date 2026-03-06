import os
import databases
import sqlalchemy
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()

assets = sqlalchemy.Table(
    "assets",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("object_storage_key", sqlalchemy.String, unique=True, nullable=False),
    sqlalchemy.Column("filename", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("mime_type", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("size_bytes", sqlalchemy.BigInteger, nullable=False),
    sqlalchemy.Column("etag", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("current_version_id", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("is_private", sqlalchemy.Boolean, default=False),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime(timezone=True),
                      server_default=sqlalchemy.func.now()),
    sqlalchemy.Column("updated_at", sqlalchemy.DateTime(timezone=True),
                      server_default=sqlalchemy.func.now()),
)

asset_versions = sqlalchemy.Table(
    "asset_versions",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("asset_id", sqlalchemy.String,
                      sqlalchemy.ForeignKey("assets.id"), nullable=False),
    sqlalchemy.Column("object_storage_key", sqlalchemy.String, unique=True, nullable=False),
    sqlalchemy.Column("etag", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime(timezone=True),
                      server_default=sqlalchemy.func.now()),
)

access_tokens = sqlalchemy.Table(
    "access_tokens",
    metadata,
    sqlalchemy.Column("token", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("asset_id", sqlalchemy.String,
                      sqlalchemy.ForeignKey("assets.id"), nullable=False),
    sqlalchemy.Column("expires_at", sqlalchemy.DateTime(timezone=True), nullable=False),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime(timezone=True),
                      server_default=sqlalchemy.func.now()),
)

engine = sqlalchemy.create_engine(
    DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://"),
    pool_pre_ping=True
)