"""Logical uploads and expiring idempotency keys; no ingestion jobs."""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("documents",
        sa.Column("document_id", sa.String(36), primary_key=True),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("object_reference", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False))
    op.create_table("upload_keys",
        sa.Column("key", sa.String(128), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.document_id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False))


def downgrade() -> None:
    op.drop_table("upload_keys")
    op.drop_table("documents")
